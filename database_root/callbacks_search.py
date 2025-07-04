from dash import dcc, html, Input, Output, State, ctx, MATCH
from utils.data_compiler import compile_atts, compile_plot
from layouts_search import manual_search, search_all, search_autos, result_search, search_exsitu
import h5rdmtoolbox as h5tbx
from utils.search_tools import search_for_att, show_datasets
from utils.helpers import ntng
from utils.tools import process_data_for_preview
from layouts import display_data_info
from utils.constants import MASTER_FILE

def get_graph(dataset_name):    #little graph util function only for use in these callbacks
    graph = compile_plot(
        path = dataset_name,
        master_file = MASTER_FILE,
        dim = 2,
        target = dataset_name,
        metric = False,
        plot_all_from_df = False
    )
    graph.update_layout(width = 1000, height = 600)
    return dcc.Graph(figure = graph)

def try_process(path, master_file):
    try:
        stored_data, plottable = process_data_for_preview(path, master_file)
        return stored_data, plottable
    except TypeError:
        return '', False
    

def register_search_callbacks(app):
    #show details from browse database section
    @app.callback(
        Output('details-bd', 'children'),
        Input('show-atts-bd', 'n_clicks'),
        State('selected-path-store', 'data')
    )
    def iamsotired(n, path):
        if n == 0:
            return ''
        else:
            formatted_atts = compile_atts(path)
            stored_data, plottable = try_process(path, MASTER_FILE)
            if plottable:
                graph = get_graph(path)
            else:
                graph = ''
            
            return display_data_info(formatted_atts, stored_data, graph)
        
    #---------------------------------------------------------------- search page section
    @app.callback(
        Output('search-page-2', 'children'),
        Input('att-filt-input', 'value')
    )
    def searchpage2(choice):
        if choice == 'aa-machine':
            return search_autos()
        elif choice == 'manual-search': 
            return manual_search()
        elif choice == 'view-all-atts':
            return search_all()
        elif choice == 'exsitu-search':
            return search_exsitu()
        
    @app.callback(
        [Output('search-page-manual', 'children'),
         Output('results-manual', 'data')],
        Input('submit-manual-search', 'n_clicks'),
        State('att-search-input', 'value'),
        State('all-or-not-manual', 'value'),
        State('lower-bound-manual', 'value'),
        State('upper-bound-manual', 'value'),
        State('exact-value-manual', 'value'),
        State('non-numeric-manual', 'value')
    )
    def manual_search_callback(n, att, filter, lowerbound, upperbound, exactvalue, nonnumeric):
        if n == 0:
            return '', ntng()
        else:
            groupsonly = True if filter == 'show-all-manual' else False
            if nonnumeric is None:
                result = search_for_att(MASTER_FILE, att, groupsonly, lowerbound, upperbound, exactvalue)
                stored = [(res.name, res.attrs) for res in result]
            else:
                result = search_for_att(MASTER_FILE, att, groupsonly, lowerbound = None, upperbound = None, exactvalue = nonnumeric)
                stored = [(res.name, res.attrs) for res in result]

            if result:
                return result_search(result, att), stored
            else:
                return html.Div([
                html.Span('No results found. Try adjusting bounds?'), 
                html.Br(), 
                html.Span('Note: there\'s a bug here that idk how to fix - try choosing "Only show groups" even if you know your result will be a dataset.')]), ntng()
            
    @app.callback(
        [Output({'type': 'search-output', 'category': MATCH}, 'children'),
         Output({'type': 'search-results', 'category': MATCH}, 'data')],
        Input({'type': 'submit-search', 'category': MATCH}, 'n_clicks'),
        State({'type': 'dropdown-att', 'category': MATCH}, 'value'),
        State({'type': 'radio-group-filter', 'category': MATCH}, 'value'),
        State({'type': 'bound-lower', 'category': MATCH}, 'value'),
        State({'type': 'bound-upper', 'category': MATCH}, 'value'),
        State({'type': 'bound-exact', 'category': MATCH}, 'value'),
        State({'type': 'non-numeric', 'category': MATCH}, 'value'),
        prevent_initial_call=True
    )
    def search_callback(n, att, filter_mode, lowerbound, upperbound, exactvalue, nonnumeric):
        if n == 0 or att is None:
            return '', ntng()
        #if user puts shit in nonnumeric box, takes priority over everything else arbitrarily to avoid collisions between numeric/nonnumeric function
        if nonnumeric is None:
            groupsonly = 'builds' in filter_mode if filter_mode else False
            result = search_for_att(MASTER_FILE, att, groupsonly, lowerbound, upperbound, exactvalue)
            stored = [(res.name, res.attrs) for res in result]
        else:
            groupsonly = 'builds' in filter_mode if filter_mode else False
            result = search_for_att(MASTER_FILE, att, groupsonly, lowerbound = None, upperbound = None, exactvalue = nonnumeric)
            stored = [(res.name, res.attrs) for res in result]

        if result:
            return result_search(result, att), stored
        else:
            return html.Div([
                html.Span('No results found. Try adjusting bounds?'), 
                html.Br(), 
                html.Span('Note: there\'s a bug here that idk how to fix - try choosing "Only show groups" even if you know your result will be a dataset.')]), ntng()
            
    @app.callback(
        Output('expanded-results', 'children'),
        Input('show-details-ssa', 'n_clicks'),
        State('att-result-checklist' , 'value')
    )
    def show_details_manual(n, selected):
        if n == 0:
            return ''
        else:
            expanded = []
            for path in selected:
                expanded.append(compile_atts(path))
                expanded.append(show_datasets(path, MASTER_FILE))
            
            return expanded
        
    @app.callback(
        Output({'type': 'dataset-preview', 'group': MATCH}, 'children'),
        Input({'type': 'dataset-dropdown', 'group': MATCH}, 'value')
    )
    def load_preview(dataset_name):
        if not dataset_name:
            return ''
        atts = compile_atts(dataset_name)
        data, plottable = try_process(dataset_name, MASTER_FILE)
        if plottable:
            graph = get_graph(dataset_name)
        else:
            graph = ''
        return display_data_info(atts, data, graph)
    
    #logic to save shit for analysis tab
    @app.callback(
        [Output('analysis-save-status', 'children'),
         Output('global-storage-1', 'data', allow_duplicate= True),
         Output('global-storage-2', 'data', allow_duplicate= True)],
        [Input('save-for-analysis', 'n_clicks'),
         Input('set-as-bm', 'n_clicks')],
        State('att-result-checklist', 'value'),
        prevent_initial_call = True
    )
    def save_for_a(n1, n2, selected):
        trigg = ctx.triggered_id
        if n1 == n2 == 0:
            return ntng(), ntng(), ntng()
        
        if trigg == 'save-for-analysis':
            return html.Span('Selected data saved to global storage. Load in "Analyze data" tab.', style = {'color': 'green'}), ntng(), selected
        elif trigg == 'set-as-bm':
            if len(selected) > 1:
                return html.Span('Cannot set >1 item as benchmark for comparison. Try "Save all for analysis" or select a single item', style = {'color': 'red'}), ntng(), ntng()
            else:
                return html.Span('Selected data set as benchmark for comparison. Load in "Analyze data" tab.', style = {'color': 'green'}), selected, ntng()