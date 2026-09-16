import streamlit as st
from auth import register_user, login_user


def show_login():
    st.markdown(
        """
        <style>
        .login-box {
            max-width: 500px;
            margin: 70px auto;
            padding: 35px;
            border-radius: 18px;
            background: #161a22;
            border: 1px solid #303642;
        }

        .login-title {
            text-align: center;
            font-size: 32px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .login-subtitle {
            text-align: center;
            color: #9ca3af;
            margin-bottom: 30px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="login-box">', unsafe_allow_html=True)

    st.markdown(
        '<div class="login-title">💊 Medicine Stock AI</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="login-subtitle">Intelligent Inventory Management System</div>',
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

    # ================= LOGIN =================

    with tab1:
        st.subheader("Login")

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            use_container_width=True,
            key="login_button"
        ):
            if not username or not password:
                st.warning("Please enter username and password.")
            else:
                success, role = login_user(username, password)

                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username.strip().lower()
                    st.session_state.role = role

                    st.success("Login successful!")

                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    # ================= REGISTER =================

    with tab2:
        st.subheader("Create Account")

        new_username = st.text_input(
            "Username",
            key="register_username"
        )

        new_password = st.text_input(
            "Password",
            type="password",
            key="register_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="confirm_password"
        )

        role = st.selectbox(
            "Select Role",
            [
                "Admin",
                "Pharmacy Staff"
            ],
            key="register_role"
        )

        if st.button(
            "Create Account",
            use_container_width=True,
            key="register_button"
        ):
            if not new_username or not new_password:
                st.warning("Please fill all required fields.")

            elif len(new_password) < 6:
                st.warning("Password must be at least 6 characters.")

            elif new_password != confirm_password:
                st.error("Passwords do not match.")

            else:
                success, message = register_user(
                    new_username,
                    new_password,
                    role
                )

                if success:
                    st.success(message)
                    st.info("Now go to the Login tab and sign in.")
                else:
                    st.error(message)

    st.markdown("</div>", unsafe_allow_html=True)