import re
import pandas as pd

# ---------------------------------------------------------------------------
# Module: preprocessor.py
# Description: Parses raw WhatsApp chat exports into a pandas DataFrame.
# ---------------------------------------------------------------------------

def preprocess(raw_data: str) -> pd.DataFrame:
    """
    Convert raw WhatsApp export text into a DataFrame with columns:
      - message_date: pandas.Timestamp
      - user: str (username or 'group_notification')
      - message: str
      - year, month, month_num, day, hour, minute, weekday (derived)
    """
    # Regex pattern to split date prefixes (e.g. "4/2/22, 18:24 - ")
    pattern = r'(\d{1,2}/\d{1,2}/\d{2}, \d{1,2}:\d{2} - )'
    parts = re.split(pattern, raw_data)[1:]  # First element is header text if any

    records = []  # Each record = (date_str, user, message)
    for date_str, message_str in zip(parts[0::2], parts[1::2]):
        date_str = date_str.strip(' -')
        message_str = message_str.strip('\n')

        # Separate user and message
        if ': ' in message_str:
            user, message = message_str.split(': ', 1)
        else:
            user, message = 'group_notification', message_str

        records.append((date_str, user, message))

    # Create DataFrame
    df = pd.DataFrame(records, columns=['message_date', 'user', 'message'])

    # Parse dates
    df['message_date'] = pd.to_datetime(
        df['message_date'],
        format='%d/%m/%y, %H:%M',
        dayfirst=True,
        errors='coerce'
    )

    # Drop rows where date parsing failed
    df.dropna(subset=['message_date'], inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Add datetime-related features
    df['year'] = df['message_date'].dt.year
    df['month'] = df['message_date'].dt.month_name()
    df['month_num'] = df['message_date'].dt.month
    df['day'] = df['message_date'].dt.day
    df['hour'] = df['message_date'].dt.hour
    df['minute'] = df['message_date'].dt.minute
    df['weekday'] = df['message_date'].dt.day_name()
    df['only_date'] = df['message_date'].dt.date  # for daily timeline

    return df

def daily_timeline(selected_user: str, data: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a timeline of message counts per day.
    """
    if selected_user != 'Overall':
        data = data[data['user'] == selected_user]

    timeline = data.groupby('only_date')['message'].count().reset_index()
    timeline.rename(columns={'message': 'message_count'}, inplace=True)

    return timeline
