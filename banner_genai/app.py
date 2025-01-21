import gradio as gr

# from utils.firestore import init_document_store
from blocks import (
    ui_about_tab,
    ui_demo_tab_assetlibrary,
    ui_demo_tab_assetcreation,
    ui_demo_tab_assetpreprocess,
    ui_demo_bannertemplateconfig_tab,
    ui_demo_tab_bannergen,
)
# TODO: Init firestore documents from local artefacts.
# config_file_path = "./Artefacts/Config/config.json"
# init_document_store(config_file_path)

tabs = [
    (ui_about_tab, "About"),
    (ui_demo_tab_assetlibrary, "Demo Asset Library"),
    (ui_demo_tab_assetcreation, "Demo Asset Creation"),
    (ui_demo_tab_assetpreprocess, "Demo Asset Preprocessing"),
    (ui_demo_bannertemplateconfig_tab, "Demo Banner Template"),
    (ui_demo_tab_bannergen, "Demo Banner Generation"),
]
interfaces, tab_names = zip(*tabs)
demo = gr.TabbedInterface(interface_list=interfaces, tab_names=tab_names)

if __name__ == "__main__":
    demo.launch(debug=True)
