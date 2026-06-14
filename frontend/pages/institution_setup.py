import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

def institution_setup_page():
    st.title("Institution Setup")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Add New Institution")

        with st.form("add_form"):
            name = st.text_input("Institution Name")
            size = st.selectbox("Size", ["Small", "Medium", "Large"])
            submitted = st.form_submit_button("Add")

            if submitted and name:
                try:
                    response = requests.post(
                        f"{API_URL}/api/institutions/",
                        json={"name": name, "size": size}
                    )
                    if response.status_code == 201:
                        st.success(f"Added: {name}")
                        st.rerun()
                    else:
                        error = response.json().get("detail", "Unknown error")
                        st.error(f"Failed: {error}")
                except:
                    st.error("Backend not running on port 8000")

    with col2:
        st.subheader("Current Institutions")

        try:
            response = requests.get(f"{API_URL}/api/institutions/")
            if response.status_code == 200:
                data = response.json()
                if data:
                    df = pd.DataFrame(data)[["institution_id", "name", "size"]]
                    df.columns = ["ID", "Name", "Size"]
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    st.info(f"Total: {len(data)} institutions")
                else:
                    st.info("No institutions yet")
        except:
            st.error("Cannot connect to backend")

    st.markdown("---")
    with st.expander("Delete Institution"):
        try:
            response = requests.get(f"{API_URL}/api/institutions/")
            if response.status_code == 200:
                data = response.json()
                if data:
                    options = {f"{inst['name']} ({inst['institution_id']})": inst['institution_id'] for inst in data}
                    selected = st.selectbox("Select to delete", list(options.keys()))
                    if st.button("Delete"):
                        inst_id = options[selected]
                        delete_resp = requests.delete(f"{API_URL}/api/institutions/{inst_id}")
                        if delete_resp.status_code == 204:
                            st.success("Deleted successfully")
                            st.rerun()
                        else:
                            st.error("Delete failed")
        except:
            st.error("Cannot connect to backend")

if __name__ == "__main__":
    institution_setup_page()