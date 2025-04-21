import streamlit as st
import preprocessor, helper
import matplotlib.pyplot as plt
import seaborn as sns

# Streamlit UI setup
st.sidebar.title("WhatsApp Chat Analyzer")

# File uploader for .txt chat exports
uploaded_file = st.sidebar.file_uploader("Choose a WhatsApp chat file (.txt)", type=["txt"])

if uploaded_file is not None:
    # Decode uploaded bytes to string
    bytes_data = uploaded_file.getvalue()
    data = bytes_data.decode("utf-8")

    # Preprocess chat export into DataFrame
    df = preprocessor.preprocess(data)

    # Build a list of users (exclude group notifications)
    user_list = df['user'].unique().tolist()
    if 'group_notification' in user_list:
        user_list.remove('group_notification')
    user_list.sort()
    user_list.insert(0, "Overall")

    # Sidebar selectbox for user-level or overall analysis
    selected_user = st.sidebar.selectbox("Show analysis for", user_list)

    # When button clicked, generate all analyses
    if st.sidebar.button("Show Analysis"):

        # --- Top Statistics ---
        st.title("Top Statistics")
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Messages", num_messages)
        col2.metric("Total Words", words)
        col3.metric("Media Shared", num_media_messages)
        col4.metric("Links Shared", num_links)

        # --- Monthly Timeline ---
        st.title("Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(timeline['time'], timeline['message'], color='green')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # --- Daily Timeline ---
        st.title("Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # --- Activity Map ---
        st.title('Activity Map')
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Most Busy Day")
            busy_day = helper.week_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values, color='purple')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        with col2:
            st.subheader("Most Busy Month")
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values, color='orange')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        # --- Weekly Activity Heatmap ---
        st.title("Weekly Activity Heatmap")
        user_heatmap = helper.activity_heatmap(selected_user, df)
        fig, ax = plt.subplots()
        sns.heatmap(user_heatmap, ax=ax)
        st.pyplot(fig)

        # --- Most Busy Users (group level) ---
        if selected_user == 'Overall':
            st.title("Most Busy Users")
            x, new_df = helper.most_busy_users(df)
            col1, col2 = st.columns(2)

            with col1:
                fig, ax = plt.subplots()
                ax.bar(x.index, x.values, color='red')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)

            with col2:
                st.dataframe(new_df)

        # --- WordCloud ---

        # --- Most Common Words ---
        st.title("Most Common Words")
        most_common_df = helper.most_common_words(selected_user, df)
        # fig, ax = plt.subplots()
        # ax.barh(most_common_df[0], most_common_df[1])
        # plt.xticks(rotation='horizontal')
        # st.pyplot(fig)
        print(most_common_df.head())
        fig, ax = plt.subplots()
        ax.barh(most_common_df['word'], most_common_df['count'])
        ax.invert_yaxis()               # optional: largest bar on top
        ax.set_xlabel('Count')
        ax.set_ylabel('Word')
        ax.set_title('Most Common Words')

        st.pyplot(fig)
        # --- Emoji Analysis ---
        st.title("Emoji Analysis")
        emoji_df = helper.emoji_helper(selected_user, df)
        if not emoji_df.empty:
            col1, col2 = st.columns(2)
        
            with col1:
                st.write("Emoji Frequencies:") # Add context
                # Display the DataFrame (already correct)
                st.dataframe(emoji_df)
        
            with col2:
                st.write("Top 5 Emoji Distribution:") # Add context
                fig, ax = plt.subplots()
                # --- FIX: Use column names 'frequency' and 'emoji' ---
                ax.pie(
                    emoji_df['frequency'].head(),      # Use the 'frequency' column for values
                    labels=emoji_df['emoji'].head(),  # Use the 'emoji' column for labels
                    autopct="%0.2f%%"
                )
                # --- END FIX ---
                st.pyplot(fig)
        else:
            # Handle the case where no emojis were found
            st.write("No emojis found for this selection.")
