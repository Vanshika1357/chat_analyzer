import pandas as pd
from urlextract import URLExtract
from wordcloud import WordCloud
from collections import Counter
import emoji

# Initialize URL extractor
extractor = URLExtract()

# ---------------------------------------------------------------------------
# Module: helper.py
# Description: Provides analysis functions for WhatsApp chat DataFrame.
# ---------------------------------------------------------------------------

def fetch_stats(selected_user: str, df: pd.DataFrame):
    """Return counts: messages, words, media messages, and links."""
    data = df.copy()
    if selected_user != 'Overall':
        data = data[data['user'] == selected_user]

    num_messages = data.shape[0]
    words = data['message'].apply(lambda msg: len(msg.split())).sum()
    num_media_messages = data[data['message'] == '<Media omitted>'].shape[0]
    num_links = data['message'].apply(lambda msg: len(extractor.find_urls(msg))).sum()
    return num_messages, words, num_media_messages, num_links


def most_busy_users(df: pd.DataFrame):
    """Return Series of top users by message count and DataFrame of percentages."""
    user_counts = df['user'].value_counts().drop('group_notification', errors='ignore')
    total_msgs = user_counts.sum()
    percent_df = (user_counts / total_msgs * 100).round(2).reset_index()
    percent_df.columns = ['user', 'percent']
    return user_counts, percent_df


def create_wordcloud(selected_user: str, df: pd.DataFrame):
    """Generate a wordcloud for selected user (or overall), excluding stopwords."""
    # Load stopwords
    with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
        stop_words = set(f.read().split())

    data = df.copy()
    if selected_user != 'Overall':
        data = data[data['user'] == selected_user]

    # Filter out system messages and media
    data = data[~data['message'].str.contains('<Media omitted>')]

    # Remove stop words
    def remove_stops(text):
        return ' '.join([word for word in text.lower().split() if word not in stop_words])

    cleaned = data['message'].apply(remove_stops).str.cat(sep=' ')
    wc = WordCloud(width=500, height=500, min_font_size=10, background_color='white')
    return wc.generate(cleaned)


def most_common_words(selected_user: str, df: pd.DataFrame):
    """Return DataFrame of top 20 most common words, excluding stopwords and non-alpha."""
    with open('stop_hinglish.txt', 'r', encoding='utf-8') as f:
        stop_words = set(f.read().split())

    data = df.copy()
    if selected_user != 'Overall':
        data = data[data['user'] == selected_user]

    # Exclude system and media messages
    temp = data[~data['message'].str.contains('<Media omitted>')]
    temp = temp[~temp['message'].str.contains('http')]

    words = []
    for msg in temp['message']:
        for w in msg.lower().split():
            if w.isalpha() and w not in stop_words:
                words.append(w)

    common = Counter(words).most_common(20)
    return pd.DataFrame(common, columns=['word', 'count'])


def emoji_helper(selected_user: str, df: pd.DataFrame):
    """Return DataFrame of emojis and their frequencies."""

    data = df.copy()

    if selected_user != 'Overall':
        data = data[data['user'] == selected_user]

    emojis_list = []
    for msg in data['message']:
        # Check if the character is in the keys of emoji.EMOJI_DATA
        emojis_list.extend([ch for ch in msg if ch in emoji.EMOJI_DATA])

    # --- Add code to count frequencies and create DataFrame ---
    # Check if any emojis were found
    if not emojis_list:
         return pd.DataFrame(columns=['emoji', 'frequency']) # Return empty DF if no emojis

    # Count the frequency of each emoji
    emoji_counts = Counter(emojis_list)

    # Convert the Counter object to a DataFrame
    emoji_df = pd.DataFrame(emoji_counts.items(), columns=['emoji', 'frequency'])

    # Optional: Sort the DataFrame by frequency in descending order
    emoji_df = emoji_df.sort_values(by='frequency', ascending=False)

    return emoji_df


def monthly_timeline(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame grouped by year and month for timeline plotting."""
    data = df.copy()
    if selected_user != 'Overall':
        data = data[data['user'] == selected_user]

    timeline = (
        data
        .groupby(['year', 'month_num', 'month'])['message']
        .count()
        .reset_index()
    )
    timeline['time'] = timeline.apply(lambda x: f"{x['month']} {x['year']}", axis=1)
    return timeline


def daily_timeline(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame of daily message counts."""
    data = df.copy()
    if selected_user != 'Overall':
        data = data[data['user'] == selected_user]

    daily = (
        data.groupby('only_date')['message']
        .count()
        .reset_index()
    )
    return daily


def week_activity_map(selected_user: str, df: pd.DataFrame) -> pd.Series:
    """Return message counts for each weekday."""
    data = df.copy()
    if selected_user != 'Overall':
        data = data[data['user'] == selected_user]
    return data['weekday'].value_counts()


def month_activity_map(selected_user: str, df: pd.DataFrame) -> pd.Series:
    """Return message counts for each month name."""
    data = df.copy()
    if selected_user != 'Overall':
        data = data[data['user'] == selected_user]
    return data['month'].value_counts()


def activity_heatmap(selected_user: str, df: pd.DataFrame) -> pd.DataFrame:
    """Return pivot table heatmap of weekday vs hourly periods."""
    data = df.copy()
    if selected_user != 'Overall':
        data = data[data['user'] == selected_user]

    # Create period column (e.g., '0-1', '1-2', ..., '23-0')
    data['period'] = data['hour'].apply(lambda h: f"{h}-{(h+1)%24}")

    heatmap = (
        data.pivot_table(
            index='weekday', columns='period', values='message', aggfunc='count'
        )
        .fillna(0)
    )
    # Ensure weekday order
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap = heatmap.reindex(weekdays)
    return heatmap
