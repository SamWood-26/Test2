import streamlit as st
import os
import pandas as pd
from noLLM_analysis import *
#show more how it reaches the decision with stats and other stuff
#be able to upload file to run multiple
#have user upload API key
st.title("No LLM")


if "species" not in st.session_state:
    st.session_state.species = None
if "tissue" not in st.session_state:
    st.session_state.tissue = ["All"]
if "marker_genes" not in st.session_state:
    st.session_state.marker_genes = ""
if "background_context" not in st.session_state:
    st.session_state.background_context = ""
if "Gene_denominator" not in st.session_state:
    st.session_state.Gene_denominator = ""
if "custom_data" not in st.session_state:
   st.session_state.custom_data = ""

#Selecting type
# fit_option = st.radio(
#     "Select Option",
#     ("Inverse Weighting", "Exact Match", "Data Base"),
# )
fit_option = st.session_state.background_context

#Preset variables in some cases not all used
tissue_type = None
species = None
dataset = None
custom_genes = None

#Pre subsets the data
@st.cache_data
def get_data():
    df = load_data()
    df_human = df[df['Species'] == 'Homo sapiens']
    df_mouse = df[df['Species'] == 'Mus musculus']

    total_cells = df['Cell_standard'].nunique()
    human_cells = df_human['Cell_standard'].nunique()
    mouse_cells = df_mouse['Cell_standard'].nunique()
    return df, df_human, df_mouse, total_cells, human_cells, mouse_cells

df, df_human, df_mouse, total_cells, human_cells, mouse_cells = get_data()

#if loops that seperate inputs required base on different selections
if fit_option == "Base":
    #Species selection
    species = st.session_state.species

    if species == 'Homo sapiens':
        df_selected = df_human
        total_species_cells = human_cells
    else:
        df_selected = df_mouse
        total_species_cells = mouse_cells
    
    st.write(f"Total unique cell types before filtering: {total_cells}")
    st.write(f"After selecting {species}: {total_species_cells} unique cell types remain.")

    #Tissue type selection via searchable box
    tissue_options = get_all_tissues(df_selected, species)
    selected_tissues = st.session_state.tissue 
    tissue_type = selected_tissues if selected_tissues else None  #Assigns selected tissues
    # Filter dataset based on selected tissues
    if "All" not in selected_tissues:
        df_selected = df_selected[df_selected['Tissue_standard'].isin(selected_tissues)]
    
    # Count remaining unique cell types after filtering by tissue
    remaining_cells = df_selected['Cell_standard'].nunique()
    st.write(f"After selecting tissue type(s) {', '.join(selected_tissues)}: {remaining_cells} unique cell types remain.")


else:
    species = st.session_state.species
    tissue_type = st.session_state.tissue
    dataset = st.radio(
        "Select Dataset",
        ("Mouse Liver", "Human Breast Cancer", "Custom")
    )
    if fit_option == "Mouse Liver":
        file_path = 'feature.clean.MouseLiver1Slice1.tsv'
        #species = 'Mouse'
        #tissue_type = ['Liver']
    elif fit_option == "Human Breast Cancer":
        file_path = 'Xenium_FFPE_Human_Breast_Cancer_Rep1_panel.tsv'
        #species = 'Human'
        #tissue_type = ['Breast']

    if fit_option == "Custom Input":
        dataset = "Cutstom"
        species = st.session_state.species

        if species == 'Homo sapiens':
            tissue_options = get_all_tissues(df_human, 'Homo sapiens')
        else:
            tissue_options = get_all_tissues(df_mouse, 'Mus musculus')
        
        selected_tissues = st.session_state.tissue
        tissue_type = selected_tissues if selected_tissues else None  #Assigns selected tissues for custom cases

        custom_genes = st.session_state.marker_genes
    if fit_option == "Upload TSV File":
        species = st.session_state.species
        selected_tissues = st.session_state.tissue
        tissue_type = selected_tissues if selected_tissues else None
        custom_genes = st.session_state.marker_genes

#Marker genes input area
marker_genes_input = st.session_state.marker_genes

#Another if/else statements based on selections
if st.button("Submit"):
    marker_genes = marker_genes_input
    if fit_option == "Base":
        if species == 'Homo sapiens':
            df_selected = df_human
        else:
            df_selected = df_mouse

        if tissue_type == "All":
            tissue_type = None


        cell_type_markers = (
            df_selected.groupby("Cell_standard")["Cell_Marker"]
            .apply(lambda x: set(x.str.split(",").sum()))  # Convert to set of genes
            .to_dict()
        )

        exact_match_result = infer_top_cell_standards(df_selected, tissue_type, marker_genes)
        exact_match_result = pd.DataFrame(exact_match_result)

        # Getting cell types
        inverse_cell_types = infer_top_cell_standards_weighted(df_selected, tissue_type, marker_genes)
        exact_cell_types = infer_top_cell_standards(df_selected, tissue_type, marker_genes)

        # Combine cell types from both methods
        relevant_cells = set(inverse_cell_types).union(set(exact_cell_types))
        cell_type_markers_filtered = {cell: cell_type_markers[cell] for cell in relevant_cells if cell in cell_type_markers}

        # Compute posterior probabilities
        posterior_probs_df = compute_posterior_probabilities(set(marker_genes), cell_type_markers_filtered)

        exact_match_result.rename(columns={exact_match_result.columns[0]: 'Cell Type'}, inplace=True)

        exact_match_result = exact_match_result.merge(posterior_probs_df, on="Cell Type", how="outer")

        # Handle NaN values if necessary (fill with a default value, such as 0)
        exact_match_result.fillna({"Probability": 0}, inplace=True)
        exact_match_result.reset_index(drop=True, inplace=True)

        # Display both results
        st.write(f"### Results for {species} with Tissue Type: {tissue_type} and Marker Genes: {marker_genes}")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Inverse Weighting")
            st.write(inverse_cell_types)

        with col2:
            st.subheader("Exact Match")
            st.write(exact_cell_types)
            exact_match_result_sorted = exact_match_result.sort_values(by='Probability', ascending=False)
            st.write(exact_match_result[['Cell Type', 'Probability']])
    else:
        if dataset == "Custom":
            custom_genes_array = string_to_gene_array(st.session_state.custom_data)
            try:
                result = predict_cell_type_with_custom_genes(species, tissue_type, custom_genes_array, marker_genes)
                st.write(f"Gene Markers Considered: {', '.join(marker_genes)}")
                st.write(f"Species: {species}, Tissue Type: {', '.join(tissue_type)}")
                st.write("Predicted Cell Types:")
                st.write(result)
            except Exception as e:
                st.write(f"Error processing custom data: {e}")
        elif dataset == "TSV input":
            custom_genes_array = st.session_state.Gene_denominator
            try:
                result = predict_cell_type_with_custom_genes(species, tissue_type, custom_genes_array, marker_genes)
                st.write(f"Gene Markers Considered: {', '.join(marker_genes)}")
                st.write(f"Species: {species}, Tissue Type: {', '.join(tissue_type)}")
                st.write("Predicted Cell Types:")
                st.write(result)
            except Exception as e:
                st.write(f"Error processing custom data: {e}")
        else:
            gene_markers = load_gene_markers(file_path)

            matched_genes = set(marker_genes) & set(gene_markers)
            dropped_genes = set(marker_genes) - matched_genes

            result = predict_cell_type(species, tissue_type, list(matched_genes))

            st.write(f"Results based off marker genes considered: {', '.join(matched_genes)}")
            if dropped_genes:
                st.write(f"Marker genes dropped out: {', '.join(dropped_genes)}")
            st.write(f"Species: {species}, Tissue Type: {tissue_type}")
            st.write("Predicted Cell Types:")
            st.write(result)



#OLD
# import streamlit as st
# import os
# import pandas as pd
# from noLLM_analysis import *
# #show more how it reaches the decision with stats and other stuff
# #be able to upload file to run multiple
# #have user upload API key
# st.title("No LLM")


# if "species" not in st.session_state:
#     st.session_state.species = None
# if "tissue" not in st.session_state:
#     st.session_state.tissue = ["All"]
# if "marker_genes" not in st.session_state:
#     st.session_state.marker_genes = ""

# #Selecting type
# fit_option = st.radio(
#     "Select Option",
#     ("Inverse Weighting", "Exact Match", "Data Base"),
# )

# #Preset variables in some cases not all used
# tissue_type = None
# species = None
# dataset = None
# custom_genes = None

# #Pre subsets the data
# @st.cache_data
# def get_data():
#     df = load_data()
#     df_human = df[df['Species'] == 'Homo sapiens']
#     df_mouse = df[df['Species'] == 'Mus musculus']

#     total_cells = df['Cell_standard'].nunique()
#     human_cells = df_human['Cell_standard'].nunique()
#     mouse_cells = df_mouse['Cell_standard'].nunique()
#     return df, df_human, df_mouse, total_cells, human_cells, mouse_cells

# df, df_human, df_mouse, total_cells, human_cells, mouse_cells = get_data()

# #if loops that seperate inputs required base on different selections
# if fit_option != "Data Base":
#     #Species selection
#     species = st.session_state.species

#     if species == 'Homo sapiens':
#         df_selected = df_human
#         total_species_cells = human_cells
#     else:
#         df_selected = df_mouse
#         total_species_cells = mouse_cells
    
#     st.write(f"Total unique cell types before filtering: {total_cells}")
#     st.write(f"After selecting {species}: {total_species_cells} unique cell types remain.")

#     #Tissue type selection via searchable box
#     tissue_options = get_all_tissues(df_selected, species)
#     selected_tissues = st.session_state.tissue 
#     tissue_type = selected_tissues if selected_tissues else None  #Assigns selected tissues
#     # Filter dataset based on selected tissues
#     if "All" not in selected_tissues:
#         df_selected = df_selected[df_selected['Tissue_standard'].isin(selected_tissues)]
    
#     # Count remaining unique cell types after filtering by tissue
#     remaining_cells = df_selected['Cell_standard'].nunique()
#     st.write(f"After selecting tissue type(s) {', '.join(selected_tissues)}: {remaining_cells} unique cell types remain.")


# else:
#     species = None
#     tissue_type = None

#     dataset = st.radio(
#         "Select Dataset",
#         ("Mouse Liver", "Human Breast Cancer", "Custom")
#     )
#     if dataset == "Mouse Liver":
#         file_path = 'feature.clean.MouseLiver1Slice1.tsv'
#         species = 'Mouse'
#         tissue_type = ['Liver']
#     elif dataset == "Human Breast Cancer":
#         file_path = 'Xenium_FFPE_Human_Breast_Cancer_Rep1_panel.tsv'
#         species = 'Human'
#         tissue_type = ['Breast']

#     if dataset == "Custom":
#         species = st.session_state.species

#         if species == 'Homo sapiens':
#             tissue_options = get_all_tissues(df_human, 'Homo sapiens')
#         else:
#             tissue_options = get_all_tissues(df_mouse, 'Mus musculus')
        
#         selected_tissues = st.session_state.tissue
#         tissue_type = selected_tissues if selected_tissues else None  #Assigns selected tissues for custom cases

#         custom_genes = st.text_area(
#             "Enter Custom data set",
#             placeholder="Enter marker genes, separated by commas. Ex: Gpx2, Rps12, Rpl12, Eef1a1, Rps19, Rpsa, Rps3, "
#             "Rps26, Rps24, Rps28, Reg4, Cldn2, Cd24a, Zfas1, Stmn1, Kcnq1, Rpl36a-ps1, Hopx, Cdca7, Smoc2"
#         )

# #Marker genes input area
# marker_genes_input = st.session_state.marker_genes

# #Another if/else statements based on selections
# if st.button("Submit"):
#     marker_genes = marker_genes_input


#     if fit_option == "Data Base":

#         if dataset == "Custom":
#                 custom_genes_array = string_to_gene_array(custom_genes)
#                 try:
#                     result = predict_cell_type_with_custom_genes(species, tissue_type, custom_genes_array, marker_genes)
#                     st.write(f"Gene Markers Considered: {', '.join(marker_genes)}")
#                     st.write(f"Species: {species}, Tissue Type: {', '.join(tissue_type)}")
#                     st.write("Predicted Cell Types:")
#                     st.write(result)
#                 except Exception as e:
#                     st.write(f"Error processing custom data: {e}")
#         else:
#             gene_markers = load_gene_markers(file_path)

#             #Finds intersection of input marker genes and loaded gene markers
#             matched_genes = set(marker_genes) & set(gene_markers)
#             dropped_genes = set(marker_genes) - matched_genes

#             #Predict cell type based on matched genes and dataset
#             result = predict_cell_type(species, tissue_type, list(matched_genes))

#             st.write(f"Results based off marker genes considered: {', '.join(matched_genes)}")
#             if dropped_genes:
#                 st.write(f"Marker genes dropped out: {', '.join(dropped_genes)}")
#             st.write(f"Species: {species}, Tissue Type: {tissue_type}")
#             st.write("Predicted Cell Types:")
#             st.write(result)

#     else:
#         if species == 'Homo sapiens':
#             df_selected = df_human
#         else:
#             df_selected = df_mouse

#         if tissue_type == "All":
#             tissue_type = None

#         if fit_option == "Best Fit":
#             #Weighted output
#             result = infer_top_cell_standards_weighted(df_selected, tissue_type, marker_genes)
#         else:
#             #Unweighted ouput
#             result = infer_top_cell_standards(df_selected, tissue_type, marker_genes)

#         st.write(f"Results for {fit_option} with species {species}, tissue type {tissue_type}, and marker genes {marker_genes}:")
#         st.write(result)