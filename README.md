# Telegram Statistics
Export Statistics for a Telegram Group Chat

## How to Run
### Telegram Statistics and Word Cloud
The `src/stats.py` file contains the main function to export telegram chat word cloud and the number of questions people have responded to.

To generate word cloud and get stats, in main repo directory, run the following command in your terminal to add `src` to your `PYTHONPATH`:
```
export PYTHONPATH=${PWD}
```

Then run:
```
python src/stats.py --chat_json path_to_telegram_chat_export  --output_dir path_to_save_output_images --mask mask_image_path
```
to generate a word cloud of json data in `DATA_DIR/word_cloud.png`. Top users bar chart is also generated in output_dir as `top_users.png` where the height of the bar is the number of questions answered by the user. You can also mask your word cloud with a mask image by passing the mask image path as `--mask` argument. See [here](https://github.com/amueller/word_cloud) for some examples.

### Telegram Graph
The `src/graph.py` file contains the main function to export a graph of people connections in a telegram chat. The graph is generated using the `pyvis` library.
Every node in the graph is a user in the chat. The edges are the connections between users. If two people replied to each other in messages, they are connected.

To generate word cloud and get stats, in main repo directory, run the following command in your terminal to add `src` to your `PYTHONPATH`:
```
export PYTHONPATH=${PWD}
```

Then run:
```
python src/graph.py --chat_json path_to_telegram_chat_export --output_graph_path path_to_dump_graph --top_n number_of_top_users_to_show
```

If you ignore `--top_n`, the graph will be generated with all users in the chat. Note that the graph is not very useful if the chat is too big.

## Adding Font for Word Cloud
Use Vazir font, which may be found in the following repository, to better display Persian words alongside English words:

https://github.com/rastikerdar/vazir-font/releases

add **`Vazir.ttf`** in **`src/data`** directory