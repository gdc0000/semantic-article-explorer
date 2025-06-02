# app/app.py
import streamlit as st
import pandas as pd
import numpy as np

# Import modules from the app package
import data_manager
import search_engine
import visualization_engine

# --- Page Configuration ---
st.set_page_config(
    page_title="Semantic Article Explorer",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Load Configuration and Data ---
# This section attempts to load all necessary data at the start.
# Errors during loading are handled by data_manager and will show up as st.error.

config = data_manager.load_config()

if config is None:
    st.stop() # Stop execution if config fails to load

# Load data using functions from data_manager
# These functions use Streamlit's caching
df_articles = data_manager.load_processed_records(config['paths']['processed_data'])
faiss_index = data_manager.load_faiss_index(config)
embedding_model = data_manager.load_embedding_model(config)
# full_embeddings = data_manager.load_embeddings_array(config) # Optional, if needed

# Check if essential data loaded successfully
if df_articles.empty or faiss_index is None or embedding_model is None:
    st.error("Essential data (articles, index, or model) could not be loaded. Please check the logs and ensure preprocessing was successful.")
    st.stop()

# --- Application State Initialization ---
# Using st.session_state to store persistent state across reruns
if 'selected_article_index' not in st.session_state:
    st.session_state.selected_article_index = None # DataFrame index of the clicked article
if 'neighbor_indices' not in st.session_state:
    st.session_state.neighbor_indices = [] # DataFrame indices of neighbors
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'last_clicked_id' not in st.session_state: # To track clicks on plot points
    st.session_state.last_clicked_id = None


# --- Helper Functions ---
def display_article_details(article_series, max_abstract_length):
    """Displays details of a selected article."""
    if article_series is None or article_series.empty:
        st.info("Select an article from the map or search results to see details.")
        return

    st.subheader(f"📄 {article_series.get('title', 'N/A')}")

    authors = article_series.get('authors', 'N/A')
    if isinstance(authors, list):
        authors = ", ".join(authors)

    year = article_series.get('year', 'N/A')
    if year == 0: year = "N/A" # From cleaning step

    journal = article_series.get('journal', 'N/A')

    st.markdown(f"""
    **ID:** {article_series.get('id', 'N/A')} <br>
    **Authors:** {authors} <br>
    **Year:** {year} <br>
    **Journal:** {journal}
    """, unsafe_allow_html=True)

    abstract = article_series.get('abstract', 'No abstract available.')
    if len(abstract) > max_abstract_length:
        with st.expander("Read full abstract..."):
            st.write(abstract)
        st.write(abstract[:max_abstract_length] + "...")
    else:
        st.write(abstract)

def perform_search(query, df_articles_ref, model, index, top_k, query_prefix=""):
    """Performs semantic search and updates session state."""
    if not query:
        st.session_state.selected_article_index = None
        st.session_state.neighbor_indices = []
        return

    query_embedding = search_engine.embed_query(query, model, query_prefix)
    if query_embedding is None:
        st.warning("Could not generate embedding for the query.")
        st.session_state.selected_article_index = None
        st.session_state.neighbor_indices = []
        return

    distances, neighbor_original_indices = search_engine.search_faiss_index(query_embedding, index, top_k=top_k + 1) # +1 to potentially exclude self if query is an article title

    if neighbor_original_indices is None or len(neighbor_original_indices) == 0:
        st.info("No similar articles found for your query.")
        st.session_state.selected_article_index = None
        st.session_state.neighbor_indices = []
        return

    # Convert FAISS indices (which are row numbers in the original embeddings array)
    # to DataFrame indices if they are different (e.g., if df_articles was filtered).
    # Here, we assume df_articles is the full, unfiltered dataset that matches FAISS.
    # The indices from FAISS directly correspond to rows in df_articles.
    
    # Check if the query itself is very similar to one of the results (e.g. if user pasted a title)
    # This is a simple check; more robust would involve comparing query text to titles.
    # For now, we assume the first result is the "query" if it's very close.
    # A better approach for "find similar to this article" is to use an article ID.

    # The indices from FAISS are direct indices into the `df_articles` DataFrame
    # because `df_articles` was used to generate embeddings in that order.
    st.session_state.selected_article_index = neighbor_original_indices[0] # Closest match as "selected"
    st.session_state.neighbor_indices = neighbor_original_indices[1:top_k+1] # The rest as neighbors


def find_similar_to_selected(selected_df_idx, df_articles_ref, model, index, top_k, passage_prefix=""):
    """Finds articles similar to a currently selected article (by its DataFrame index)."""
    if selected_df_idx is None:
        return

    selected_article_series = df_articles_ref.loc[selected_df_idx]
    
    # Combine title and abstract for embedding, similar to preprocessing
    text_to_embed = ""
    for field in config['embedding_model']['text_fields_to_embed']:
        text_to_embed += selected_article_series.get(field, "") + " "
    text_to_embed = text_to_embed.strip()

    if not text_to_embed:
        st.warning("Selected article has no text content to find similars.")
        return

    # Use passage_prefix if defined, as we are embedding a "document"
    article_embedding = search_engine.embed_query(text_to_embed, model, passage_prefix)

    if article_embedding is None:
        st.warning("Could not generate embedding for the selected article.")
        return

    distances, neighbor_original_indices = search_engine.search_faiss_index(article_embedding, index, top_k=top_k + 1) # +1 to exclude self

    if neighbor_original_indices is None or len(neighbor_original_indices) == 0:
        st.info("No similar articles found.")
        st.session_state.neighbor_indices = []
        return

    # Exclude the selected article itself from its neighbors
    # The indices from FAISS are direct indices into the `df_articles` DataFrame.
    # The first result (index 0) will be the article itself.
    st.session_state.neighbor_indices = [idx for idx in neighbor_original_indices if idx != selected_df_idx][:top_k]


# --- UI Layout ---
st.title(f"🗺️ {config['app_settings']['title']}")
st.markdown("Interactive exploration of scientific articles through a 2D/3D semantic map.")

# --- Sidebar for Controls ---
with st.sidebar:
    st.header("🔎 Search & Filter")

    # Search bar
    search_query_input = st.text_input(
        "Search by keywords:",
        value=st.session_state.search_query,
        key="search_bar_input",
        on_change=lambda: setattr(st.session_state, 'search_query', st.session_state.search_bar_input) # Update state on change
    )

    if st.button("Search", key="search_button", type="primary"):
        st.session_state.search_query = st.session_state.search_bar_input # Ensure state is current
        query_prefix = config.get('embedding_model', {}).get('query_prefix', "")
        perform_search(
            st.session_state.search_query,
            df_articles,
            embedding_model,
            faiss_index,
            config['app_settings']['default_top_k'],
            query_prefix
        )
        st.session_state.last_clicked_id = None # Reset click selection on new search

    st.markdown("---")
    # Filters (optional)
    st.subheader("Filters")
    # Year filter
    if 'year' in df_articles.columns and pd.api.types.is_numeric_dtype(df_articles['year']):
        min_year, max_year = int(df_articles['year'].min()), int(df_articles['year'].max())
        if min_year < max_year : # Ensure there's a range to filter
            selected_years = st.slider(
                "Publication Year:",
                min_year, max_year,
                (min_year, max_year),
                key="year_filter"
            )
        else:
            selected_years = (min_year, max_year) # No slider if only one year or bad data
            st.caption(f"Year data: {min_year}")
    else:
        selected_years = None
        st.caption("Year data not available or not numeric for filtering.")

    # Journal filter (example - could be multi-select)
    if 'journal' in df_articles.columns:
        unique_journals = sorted(df_articles['journal'].astype(str).unique().tolist())
        if len(unique_journals) > 1:
            selected_journal = st.selectbox(
                "Journal (select 'All' to disable):",
                options=["All"] + unique_journals,
                index=0,
                key="journal_filter"
            )
        else:
            selected_journal = "All"
            st.caption(f"Journal data: {unique_journals[0] if unique_journals else 'N/A'}")

    else:
        selected_journal = "All"
        st.caption("Journal data not available for filtering.")


# --- Main Area for Visualization and Details ---
col1, col2 = st.columns([3, 2]) # Visualization takes more space

with col1:
    st.subheader("Semantic Map")

    # Apply filters to get df_display
    df_display = df_articles.copy()
    if selected_years:
        df_display = df_display[(df_display['year'] >= selected_years[0]) & (df_display['year'] <= selected_years[1])]
    if selected_journal != "All":
        df_display = df_display[df_display['journal'] == selected_journal]

    if df_display.empty:
        st.warning("No articles match the current filter criteria.")
    else:
        # Map session state indices (which are for original df_articles) to df_display indices
        # This is crucial if df_display is a filtered subset.
        # We need to find the df_display index for the selected_article_index from original df.
        
        query_point_display_idx = None
        if st.session_state.selected_article_index is not None:
            # Check if the selected article is in the filtered df_display
            if st.session_state.selected_article_index in df_display.index:
                query_point_display_idx = st.session_state.selected_article_index
            else: # If selected article is filtered out, clear selection for display
                query_point_display_idx = None


        neighbor_display_indices = []
        # if st.session_state.neighbor_indices: REMOVED
        if st.session_state.neighbor_indices is not None and len(st.session_state.neighbor_indices) > 0:

            # Filter neighbor_indices to only those present in df_display
            neighbor_display_indices = [idx for idx in st.session_state.neighbor_indices if idx in df_display.index]


        # Create the plot
        plot_fig = visualization_engine.create_semantic_map(
            df_display=df_display, # Pass the potentially filtered DataFrame
            plot_dimensions=config['app_settings']['plot_dimensions'],
            hover_name='title',
            hover_data=['id', 'year', 'journal', 'authors'],
            highlight_indices=neighbor_display_indices, # Use display indices
            query_point_index=query_point_display_idx, # Use display index
            point_size=config['app_settings']['plot_point_size'],
            map_height=600
        )
        # For handling clicks on the plot:
        # Plotly express click events return a list of points. We take the first one.
        # The `customdata` can be used to pass the original DataFrame index.
        # For simplicity, px.scatter uses the DataFrame index by default if no customdata is set.
        # We need to ensure that the index of df_display is what we want.
        # If df_display is a slice, its index will be from the original df_articles.
        
        # Add customdata to map click events back to original df_articles index
        # This is important if df_display is filtered.
        # The index of df_display IS the original index from df_articles.
        plot_fig.update_traces(customdata=df_display.index.values)


        # Display the plot and handle click events
        # `selected_points` will contain the `customdata` (original index) of the clicked point
        clicked_event = st.plotly_chart(plot_fig, use_container_width=True, on_select="rerun")

        if clicked_event.selection and clicked_event.selection["points"]:
            # `customdata` holds the original DataFrame index
            clicked_df_index = clicked_event.selection["points"][0]["customdata"]

            # Prevent re-processing if the same point is clicked repeatedly without other interaction
            # (Streamlit's on_select="rerun" can be sensitive)
            if st.session_state.last_clicked_id != clicked_df_index:
                st.session_state.selected_article_index = clicked_df_index
                st.session_state.last_clicked_id = clicked_df_index # Update last clicked
                st.session_state.search_query = df_articles.loc[clicked_df_index, 'title'] # Update search bar

                # Find similar articles to the one clicked on the map
                passage_prefix = config.get('embedding_model', {}).get('passage_prefix', "")
                find_similar_to_selected(
                    st.session_state.selected_article_index,
                    df_articles, # Use original df_articles for embedding lookup
                    embedding_model,
                    faiss_index,
                    config['app_settings']['default_top_k'],
                    passage_prefix
                )
                st.rerun() # Rerun to update plot with new selection and neighbors

with col2:
    st.subheader("Article Details & Similar Work")

    # Display details of the currently selected article
    if st.session_state.selected_article_index is not None and \
       st.session_state.selected_article_index in df_articles.index: # Check if index is valid
        selected_article_data = df_articles.loc[st.session_state.selected_article_index]
        display_article_details(selected_article_data, config['app_settings']['max_abstract_length_display'])

        # Button to find similar articles to the one displayed in details
        if st.button("Find Similar to This Article", key="find_similar_details_button"):
            passage_prefix = config.get('embedding_model', {}).get('passage_prefix', "")
            find_similar_to_selected(
                st.session_state.selected_article_index,
                df_articles,
                embedding_model,
                faiss_index,
                config['app_settings']['default_top_k'],
                passage_prefix
            )
            st.rerun() # Rerun to update plot and neighbor list
    else:
        st.info("Click on a point in the map or search to see details.")

    st.markdown("---")
    # Display list of similar articles (neighbors)
    # if st.session_state.neighbor_indices: REMOVED
    if st.session_state.neighbor_indices is not None and len(st.session_state.neighbor_indices) > 0:

        st.markdown("**Similar Articles:**")
        # Ensure neighbor indices are valid for df_articles
        valid_neighbor_indices = [idx for idx in st.session_state.neighbor_indices if idx in df_articles.index]

        for i, neighbor_idx in enumerate(valid_neighbor_indices):
            neighbor_article = df_articles.loc[neighbor_idx]
            # Make neighbor titles clickable to select them
            if st.button(f"{i+1}. {neighbor_article.get('title', 'N/A')}", key=f"neighbor_{neighbor_idx}"):
                st.session_state.selected_article_index = neighbor_idx
                st.session_state.last_clicked_id = neighbor_idx # Update last clicked
                st.session_state.search_query = neighbor_article.get('title', '') # Update search bar

                # Find new set of neighbors for this newly selected article
                passage_prefix = config.get('embedding_model', {}).get('passage_prefix', "")
                find_similar_to_selected(
                    st.session_state.selected_article_index,
                    df_articles,
                    embedding_model,
                    faiss_index,
                    config['app_settings']['default_top_k'],
                    passage_prefix
                )
                st.rerun() # Rerun to update everything
            st.caption(f"ID: {neighbor_article.get('id', 'N/A')}, Year: {neighbor_article.get('year', 'N/A')}")
    elif st.session_state.search_query or st.session_state.selected_article_index is not None:
        st.caption("No similar articles found or search not performed yet for current selection.")

# --- Footer or additional info ---
st.sidebar.markdown("---")
st.sidebar.info(
    "This app helps explore scientific articles using semantic similarity. "
    "Built with Streamlit, FAISS, SentenceTransformers, and Plotly."
)