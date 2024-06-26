import streamlit as st
import pandas as pd
import numpy as np
import requests
from PIL import Image
from io import BytesIO
from shillelagh.backends.apsw.db import connect
import datetime

connection = connect(":memory:",
                     adapter_kwargs = {
                            "gsheetsapi": { 
                            "service_account_info":  dict(st.secrets["gcp_service_account"])
                                    }
                                        }
                        )
# -- Set page config
apptitle = 'Benkei VISA'

st.set_page_config(page_title=apptitle, page_icon=":eyeglasses:")

# Title the app
st.title(apptitle)

#request Name + Main character
name_input = st.text_input("Name: ", key = 'name_input')
character_name_input = st.text_input("Main Character Name: ", key = 'character_name_input')
#name character name must be populated before app continues
if (character_name_input == '') | (name_input == ''):
    st.stop()

#Define API call and cache the data
@st.cache_data
def get_char_data(character_name_input):
    response = requests.get(f"https://api.maplestory.gg/v2/public/character/gms/{character_name_input}")
    return response

response = get_char_data(character_name_input)
if response.status_code != 200:
    st.error("Error Character not found. VISA rejected.")
    st.stop()

#Guild Main requirements
level_req = 250
legion_req = 3000
server_req = 'Kronos'

#Store main traits to display for validation
#Name
Class = response.json()['CharacterData']['Class']
Level = response.json()['CharacterData']['Level']
Legion = response.json()['CharacterData']['LegionLevel']
Server = response.json()['CharacterData']['Server']
Image_link = response.json()['CharacterData']['CharacterImageURL']
Image_response = requests.get(Image_link)
img = Image.open(BytesIO(Image_response.content))
st.image(img)
st.text(f'Class: {Class}')
st.text(f'Level: {Level}')
st.text(f'Legion: {Legion}')
st.text(f'Server: {Server}')

if Level < level_req:
    st.text("Character Level does not meet requirements: {Level} > {level_req}")
    st.stop()
if Legion < legion_req:
    st.text("Legion does not meet requirements: {Legion} >= {legion_req}")
    st.stop()
if Server != server_req:
    st.text("Wrong Server. Benkei is on {server_req}")
    st.stop()
#If conditions above met, then we proceed to collect mule information
    #Current max at 3 mules

st.text("VISA has been approved, you may submit 3 mules:")
mule_1 = st.text_input("Mule 1 Name: ", key = 'mule_1')
mule_2 = st.text_input("Mule 2 Name: ", key = 'mule_2')
mule_3 = st.text_input("Mule 3 Name: ", key = 'mule_3')


#Create dataset to upload
df_upload = pd.DataFrame({'MULE' : [mule_1, mule_2, mule_3]
})
df_upload['NAME'] = pd.Series(name_input, index = df_upload.index)
df_upload['MAIN'] = pd.Series(character_name_input, index = df_upload.index)
df_upload['MAIN_LEVEL'] = pd.Series(Level, index = df_upload.index)
df_upload['LEGION'] = pd.Series(Legion, index = df_upload.index)

#set up timestamp
load_date = datetime.datetime.now().strftime("%Y/%m/%d")
df_upload['DATE_LOADED'] = pd.Series(load_date, index = df_upload.index)

#adjust col order
col_order = ['NAME','MAIN', 'MAIN_LEVEL', 'LEGION','MULE','DATE_LOADED']
df_upload = df_upload[col_order]
#trim to non_empty Mule names
df_upload = df_upload.loc[df_upload['MULE'].ne('')]
st.text("Preview data to upload:")
st.write(df_upload)
def submit_form():
    sheet_url = st.secrets["private_gsheets_url"]
    for i, row in df_upload.iterrows():
        insert = f"""
                INSERT INTO "{sheet_url}" (NAME, MAIN, MAIN_LEVEL, LEGION, MULE, DATE_LOADED)
                VALUES ("{row['NAME']}", "{row['MAIN']}", "{row['MAIN_LEVEL']}","{row['LEGION']}","{row['MULE']}","{row['DATE_LOADED']}")
                """
        connection.execute(insert)

    #disable button after form is submitted
    st.session_state['disable_submit'] = True   

if 'disable_submit' not in st.session_state:
    st.session_state['disable_submit'] = False

button_submit = st.button("Submit Form", key = 'button_submit', on_click=submit_form, disabled=st.session_state['disable_submit'])

