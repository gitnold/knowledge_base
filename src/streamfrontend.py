import streamlit as st


#TODO: add pages for data loading and searching.


st.set_page_config(page_title="Macadamia Doctor", page_icon="🌰")
st.title("Z3 Integrations Frontend")
search_value = st.text_input("Enter Symptom", "Yellowing leaves")
st.write(f"You searched for:  {search_value}")


