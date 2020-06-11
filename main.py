import tkinter as tk
from tkinter.filedialog import askopenfilename
import re
from pandas import read_csv as pd
import json
import os.path
from requests import post


def load():
    if os.path.exists('token.txt'):
        # Read from file what line we last read
        with open('token.txt') as json_file:
            return json.load(json_file)['token']
    return False


def import_csv_data(token):
    global v
    csv_file_path = askopenfilename()
    if csv_file_path == '':
        return
    v.set(csv_file_path)
    df = pd(csv_file_path, header=1)
    df = df[df['Record Type'] == 1].reset_index()

    upload_to_gamebus(token, df)


def upload_to_gamebus(token, df):
    hed = {'Authorization': 'Bearer ' + token}
    url = 'https://api3.gamebus.eu/v2/activities?dryrun=false'

    last_read_line = read_last_read_line()
    if not last_read_line:
        last_read_line = 0

    for index, row in df.iterrows():
        if index >= last_read_line:
            time_stamp = row['Device Timestamp']
            matches = re.findall('\d{2,4}', time_stamp)
            time_stamp = matches[2] + '-' + matches[1] + '-' + matches[0] + 'T' + time_stamp[11:16]

            print(post(url, files={'activity': json.dumps(
                {"gameDescriptor": 61,
                 "dataProvider": 1,
                 "propertyInstances": [
                     {"property": 87,
                      "value": time_stamp + ':00.00000:00'},
                     {"property": 88, "value": row['Scan Glucose mmol/L']},
                     {"property": 89, "value": int(row['Scan Glucose mmol/L'] * (1 / 0.0555))}]})}, headers=hed).json())

    save_last_read_line(len(df.index))


def save_last_read_line(data):
    with open('last_read.txt', 'w') as outfile:
        json.dump({'last_read_line': data}, outfile)


def read_last_read_line():
    if os.path.exists('last_read.txt'):
        # Read from file what line we last read
        with open('last_read.txt') as json_file:
            return json.load(json_file)['last_read_line']
    return False


token = load()

root = tk.Tk()
v = tk.StringVar()
t = tk.StringVar()
entry = tk.Entry(root, textvariable=t).grid(row=1, column=1)

tk.Button(root, text='Change token', command=lambda: save_token(t.get())).grid(row=1, column=2)


def show_token(token):
    if token:
        tk.Label(root, text='File Path').grid(row=2, column=1)
        tk.Button(root, text='Browse Data Set', command=lambda: import_csv_data(token)).grid(row=2, column=2)
        t.set(token)


def save_token(new_token):
    with open('token.txt', 'w') as outfile:
        json.dump({'token': new_token}, outfile)
    show_token(new_token)


show_token(token)
tk.Button(root, text='Close', command=root.destroy).grid(row=3, column=1)
root.mainloop()
