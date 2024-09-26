import pandas as pd
import streamlit as st
from sqlite_handler import SQLViewer
import os
import pexpect
import re
from settings_reader import read_settings


class StreamlitApp:
    def __init__(self, admin_password, mongosh_allowed_commands):
        self.admin_password = admin_password
        self.mongosh_allowed_commands = mongosh_allowed_commands

        # Initialize session state
        if 'admin_logged_in' not in st.session_state:
            st.session_state.admin_logged_in = False

        if 'child' not in st.session_state:
            st.session_state.child = pexpect.spawn('mongosh', encoding='utf-8')
            st.session_state.child.expect('>')

    def set_theme(self, theme):
        with open('/Users/williamleonheart/.streamlit/config.toml', 'w') as config_file:
            config_file.write('[theme]\n')
            config_file.write(f'base="{theme}"\n')

    def main(self):
        theme = st.sidebar.toggle("Change theme")
        if theme:
            self.set_theme("light")
        else:
            self.set_theme("dark")

        # Sidebar for role selection
        st.sidebar.header("Login Options")
        role = st.sidebar.radio("Proceed as:", ["Select Role", "User", "Admin"])

        if role == "Select Role":
            st.header("Welcome to the Database Manager")

        elif role == "User":
            self.user_process()

        elif role == "Admin":
            if st.session_state.admin_logged_in:
                self.admin_process()
            else:
                self.admin_login()

    def user_process(self):
        st.sidebar.write("You are logged in as User.")
        tab1, tab2 = st.tabs(["SQLite", "MongoDB"])
        with tab1:
            self.handle_sqlite_user()
        with tab2:
            self.mongosh_process(is_admin=False)

    def admin_login(self):
        st.sidebar.header("Admin Login")
        admin_password = st.sidebar.text_input("Enter Admin Password:", type="password")
        if st.sidebar.button("Login as Admin"):
            if admin_password == self.admin_password:
                st.session_state.admin_logged_in = True
                self.admin_process()
            else:
                st.sidebar.error("Incorrect password! Try again.")

    def admin_process(self):
        st.sidebar.write("You are logged in as Admin.")
        tab1, tab2 = st.tabs(["SQLite", "MongoDB"])
        with tab1:
            self.handle_sqlite_admin()
        with tab2:
            self.mongosh_process(is_admin=True)

    def handle_sqlite_user(self):
        st.header("Choose a database to connect")
        dbs_list = os.listdir("SQLite_databases")
        df = pd.DataFrame(dbs_list, columns=['Databases'])
        st.dataframe(df, use_container_width=True, hide_index=True)

        db_name = st.text_input("Current connection")

        # Ensure the input is not empty before checking for a valid connection
        if db_name:
            if db_name in dbs_list:
                sv = SQLViewer(f"SQLite_databases/{db_name}")
                tables_in_db = sv.simple_view(f"SELECT name FROM sqlite_master WHERE type='table';")
                table_names = [item[0] for item in tables_in_db]

                # Show tables
                selected_table = st.selectbox("Select a table", options=table_names)

                if selected_table:
                    columns_in_table = sv.simple_view(f"PRAGMA table_info({selected_table});")
                    column_names = [item[1] for item in columns_in_table]

                    # Dropdown for selecting columns to display
                    selected_columns = st.multiselect("Select columns to display", options=column_names,
                                                      default=column_names)

                    # Button to execute SELECT query
                    if st.button("Execute SELECT"):
                        if selected_columns:
                            query = f"SELECT {', '.join(selected_columns)} FROM {selected_table};"
                            try:
                                df = sv.view_query_as_df(query)
                                st.dataframe(df, use_container_width=True, hide_index=True)
                            except Exception as e:
                                st.text(f"Error processing SELECT query: {str(e)}")
                        else:
                            st.text("Please select at least one column.")
            else:
                st.text("Invalid connection.")

    def handle_sqlite_admin(self):
        st.header("Choose a database to connect")
        dbs_list = os.listdir("SQLite_databases")
        df = pd.DataFrame(dbs_list, columns=['Databases'])
        st.dataframe(df, use_container_width=True, hide_index=True)

        db_name = st.text_input("Current connection")

        # Ensure the input is not empty before checking for a valid connection
        if db_name:
            if db_name in dbs_list:
                sv = SQLViewer(f"SQLite_databases/{db_name}")
                tables_in_db = sv.simple_view(f"SELECT name FROM sqlite_master WHERE type='table';")
                table_names = [item[0] for item in tables_in_db]
                df = pd.DataFrame(table_names, columns=['Tables'])
                st.dataframe(df, use_container_width=True, hide_index=True)

                # Using a form to explicitly submit the query
                with st.form("query_form"):
                    query = st.text_input("Enter query")
                    submit_query = st.form_submit_button("Run query")

                if submit_query:
                    if query.strip():  # Ensure the query is not just whitespace
                        query_lower = query.lower()
                        if query_lower.startswith(("insert", "update", "delete", "drop", "create", "alter")):
                            try:
                                sv.executor(query)
                                st.text("Query processed successfully.")
                            except Exception as e:
                                st.text(f"Error processing query: {str(e)}")
                        else:
                            try:
                                df = sv.view_query_as_df(query)
                                st.dataframe(df, use_container_width=True, hide_index=True)
                            except Exception as e:
                                st.text(f"Error processing SELECT query: {str(e)}")
                    else:
                        st.text("Please enter a valid query.")
            else:
                st.text("Invalid connection.")

    def mongosh_process(self, is_admin):
        command = st.text_area("Enter command", key='mongo_command')
        if command:
            if is_admin or command in self.mongosh_allowed_commands:
                st.session_state.child.sendline(command)
                st.session_state.child.expect('>')
                output = st.session_state.child.before
                cleaned_output = re.sub(r'\x1B[@-_][0-?]*[ -/]*[@-~]', '', output)
                cleaned_output_lines = cleaned_output.splitlines()
                if cleaned_output_lines:
                    cleaned_output_lines[-1] += ' >'
                    cleaned_output = '\n'.join(cleaned_output_lines)
                st.session_state.latest_output = cleaned_output
            else:
                st.text("This command is unavailable for you.")
        if 'latest_output' in st.session_state:
            st.code(st.session_state.latest_output, language="mongodb")


if __name__ == "__main__":
    ADMIN_PASSWORD = read_settings('settings.txt')['ADMIN_PASSWORD']
    MONGOSH_ALLOWED_COMMANDS = read_settings('settings.txt')['MONGOSH_ALLOWED_COMMANDS']

    app = StreamlitApp(ADMIN_PASSWORD, MONGOSH_ALLOWED_COMMANDS)
    app.main()
