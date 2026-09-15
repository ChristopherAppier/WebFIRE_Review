import spacy

# Load the transformer-based English model
nlp = spacy.load("en_core_web_trf")

# Test the model with a sample text
with open("/Users/chrisappier/Documents/WebFIRE_Review/ref/spacy_test_doc.txt", "r") as file:
    text = file.read()

# Process the text with the model
doc = nlp(text)

# Print the named entities found in the text
for ent in doc.ents:
    if ent.label_ in ["ORG"]:
        print(ent.text)