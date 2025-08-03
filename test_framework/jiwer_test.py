from jiwer import wer, Compose, ToLowerCase, RemovePunctuation, RemoveMultipleSpaces, Strip

def split_into_words(sentences):
    """Custom function to split sentences into words"""
    if isinstance(sentences, str):
        return sentences.split()
    return [sentence.split() for sentence in sentences]

transform = Compose([
    ToLowerCase(),
    RemovePunctuation(),
    RemoveMultipleSpaces(),
    Strip(),
    split_into_words
])

ref = "The human voice:\nIt's the instrument we all play.\nIt's the most powerful sound in the world, probably."
hyp = "the human voice. It's an instrument we all play."

print(wer(ref, hyp, reference_transform=transform, hypothesis_transform=transform))