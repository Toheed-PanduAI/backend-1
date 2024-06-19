from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def characters_to_words(characters, start_times, end_times):
    # Ensure the lengths of the lists match
    if len(characters) != len(start_times) or len(characters) != len(end_times):
        print(len(characters), len(start_times), len(end_times))
        raise ValueError("Input lists must have the same length.")

    words = []
    word_start_times = []
    word_end_times = []

    word = []
    word_start_time = None
    word_end_time = None

    for i, char in enumerate(characters):
        if char != ' ':
            if not word:
                word_start_time = start_times[i]
            word.append(char)
            word_end_time = end_times[i]
        else:
            if word:
                words.append(''.join(word))
                word_start_times.append(word_start_time)
                word_end_times.append(word_end_time)
                word = []
                word_start_time = None
                word_end_time = None

    # Add the last word if there is one
    if word:
        words.append(''.join(word))
        word_start_times.append(word_start_time)
        word_end_times.append(word_end_time)

    return {
        'words': words,
        'word_start_times': word_start_times,
        'word_end_times': word_end_times
    }