import json
import pandas as pd
from pyvis.network import Network

# Load the dataset from a JSONL file
def load_data(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as infile:
        for line in infile:
            data.append(json.loads(line))
    return pd.DataFrame(data)

file_path = 'Input_Dir'
df = load_data(file_path)

# 1. Assign Stance to Each User by Aggregating Their Comments
user_stances = df.groupby('AuthorName')['Stance_Label'].agg(lambda x: x.value_counts().idxmax()).reset_index()
user_stances.columns = ['AuthorName', 'Assigned_Stance']

# 2. Remove Users Assigned to Stance = 0
filtered_users = user_stances[user_stances['Assigned_Stance'] != 1]['AuthorName'] #Filtered
df_filtered = df[df['AuthorName'].isin(filtered_users) & (df['Stance_Label'] != 1)] #Filter

# 3. Build the Network
net = Network(height="1000px", width="100%", bgcolor="#ffffff", font_color="black", directed=True)

color_map = {
    0: 'red',
    1: 'grey',
    2: 'green'
}

# 4. Keep track of nodes with edges and edge information
nodes_with_edges = set()
edge_info = []

# Collect edge information and nodes with edges
for _, row in df_filtered.iterrows():
    if row['Response to'] in df_filtered['CommentID'].values:
        parent_author = df_filtered[df_filtered['CommentID'] == row['Response to']]['AuthorName'].values[0]

        if parent_author != row['AuthorName']:
            color = color_map.get(row['Stance_Label'], 'grey')
            edge_info.append((row['AuthorName'], parent_author, color))
            nodes_with_edges.add(row['AuthorName'])
            nodes_with_edges.add(parent_author)

    elif pd.isnull(row['Response to']):
        video_id = row['VideoID']
        edge_info.append((row['AuthorName'], video_id, 'grey'))
        nodes_with_edges.add(row['AuthorName'])
        nodes_with_edges.add(video_id)

# Add nodes with edges
for node in nodes_with_edges:
    if node in df_filtered['AuthorName'].values:
        stance = df_filtered[df_filtered['AuthorName'] == node]['Stance_Label'].iloc[0]
        color = color_map.get(stance, 'grey')
        title = f"{node} - Stance: {stance}"
        net.add_node(node, label=node, title=title, color=color)
    else:
        # This is a video node
        net.add_node(node, label=f"Video: {node}", color="black", shape="square", size=20)

# Add edges
for source, target, color in edge_info:
    net.add_edge(source, target, color=color)

# Debugging: print stance labels to confirm filtering
print(df_filtered['Stance_Label'].unique())

# Generate and display the network
net.show_buttons(filter_=['physics'])
net.show("FileName.html", notebook=False)
