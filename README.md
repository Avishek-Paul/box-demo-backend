# Box Demo Backend

A small flask server that is used to retrieve and upload files into a Box instance.

## Endpoints

**GET /folder**

Shows the following information for all items within the provided folder (defaults to 0 (root folder)): id,name, shared_link, type, num_items (child items if the item is a folder)
Shows the following information about the parent folder: id, name

**POST /folder**

Creates a folder within the specified folder id. Defaults to 0 (root folder).

**POST /upload**

Uploades a file into the provided folder (defaults to 0 (root folder)).

## Running the server
Run the following commands

```pip install -r requirements.txt```

```python app.py```
