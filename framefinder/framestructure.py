# AUTOGENERATED! DO NOT EDIT! File to edit: ../nbs/03_frame_structure.ipynb.

# %% auto 0
__all__ = ['FramingStructure']

# %% ../nbs/03_frame_structure.ipynb 0
import torch
from transformers import pipeline
import penman
from collections import Counter, defaultdict
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import pygraphviz_layout

class FramingStructure:
    def __init__(self, base_model, roles=None):
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.translator = pipeline("text2text-generation", base_model, device=device, max_length=300)

    def __call__(self, sequence_to_translate, error_type=None):
        res = self.translator(sequence_to_translate)
        def try_decode(x):
            try:
                return penman.decode(x["generated_text"])
            except:
                return error_type  # None type will be filtered below.
        graphs = list(filter(lambda item: item is not None, [try_decode(x) for x in res]))
        return graphs

    def visualize(self, decoded_graphs, min_node_threshold=1, **kwargs):
        cnt = Counter()

        for gen_text in decoded_graphs:
            amr = gen_text.triples
            amr = list(filter(lambda x: x[2] is not None, amr))
            amr = list(map(lambda x: (x[0], x[1].replace(":", ""), x[2]), amr))
            def trim_distinction_end(x):
                x = x.split("_")[0]
                return x
            amr = list(map(lambda x: (trim_distinction_end(x[0]), x[1], trim_distinction_end(x[2])), amr))
            cnt.update(amr)

        G = nx.DiGraph()

        color_map = defaultdict(lambda: "k", {
            "ARG0": "y",
            "ARG1": "r",
            "ARG2": "g",
            "ARG3": "b"
        })

        for entry, num in cnt.items():
            if not G.has_node(entry[0]):
                G.add_node(entry[0], weight=0)
            if not G.has_node(entry[2]):
                G.add_node(entry[2], weight=0)
            G.nodes[entry[0]]["weight"] += num
            G.nodes[entry[2]]["weight"] += num
            G.add_edge(entry[0], entry[2], role=entry[1], weight=num, color=color_map[entry[1]])

        G_sub = nx.subgraph_view(G, filter_node=lambda n: G.nodes[n]["weight"] >= min_node_threshold)

        node_sizes = [x * 100 for x in nx.get_node_attributes(G_sub,'weight').values()]
        edge_colors = nx.get_edge_attributes(G_sub,'color').values()

        fig = plt.figure()

        pos = pygraphviz_layout(G_sub, prog="dot")
        nx.draw_networkx(G_sub, pos, node_size=node_sizes, edge_color=edge_colors)
        nx.draw_networkx_labels(G_sub, pos)
        nx.draw_networkx_edge_labels(G_sub, pos, edge_labels=nx.get_edge_attributes(G_sub, "role"))
        plt.tight_layout()
        return fig
