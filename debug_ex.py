from src.diff.diff_analysis import DiffAnalyzer

diff_analysier = DiffAnalyzer("/home/haianhlt/Documents/bioturing/bioalpha")


diffs = diff_analysier.analyze_diffs("tk726_zarr3", "main")

print(diffs[5].get_source_code_context())