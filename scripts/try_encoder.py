import time
from gen.encoder import Encoder

SENTENCES = [
    "The quick brown fox jumps over the lazy dog, showcasing its agility and speed "
    "in the forest.",
    "She quietly opened the door to the old library, feeling a sense of awe and curiosity.",
    "The sunset painted the sky with hues of orange and pink, creating a breathtaking view.",
    "He carefully examined the ancient artifact, marveling at its intricate design and "
    "historical significance.",
    "The bustling city streets were filled with people rushing to their destinations, cars "
    "honking loudly.",
    "She sat by the window, watching the raindrops trickle down the glass, lost in "
    "her thoughts.",
    "The chef meticulously prepared the gourmet meal, ensuring each ingredient was perfectly "
    "balanced.",
    "The hikers reached the summit just as the sun began to rise, illuminating the "
    "landscape below.",
    "The old man sat on the park bench, feeding the pigeons and reminiscing about his youth.",
    "The scientist conducted the experiment with precision, documenting every step meticulously.",
    "The children played in the playground, their laughter filling the air with joy "
    "and excitement.",
    "The detective studied the crime scene, looking for any clues that might solve the mystery.",
    "The musician played the piano beautifully, captivating the audience with every note.",
    "The gardener tended to the flowers, ensuring each one received the care it needed to bloom.",
    "The athlete trained rigorously, pushing their limits to achieve their goals and dreams.",
    "The artist painted the canvas with vibrant colors, bringing her vision to life with "
    "every stroke."
]


def main():
    encoder = Encoder(batch_size=1)

    for sentence in SENTENCES:
        t0 = time.time()
        embeddings = encoder.encode([sentence])
        print(f"Sentence  : {sentence[:30]}...{sentence[-30:]} : "
              f"embeddings: {embeddings[0 , :3]} {time.time() - t0:.2f}")

    # repeat the above for a concatenation of 2 sentence pairs
    for i in range(0, len(SENTENCES), 2):
        sentence_pair = " ".join(SENTENCES[i:i + 2])
        t0 = time.time()
        embeddings = encoder.encode([sentence_pair])
        print(f"Sentence  : {sentence_pair[:30]}...{sentence_pair[-30:]} : "
              f"embeddings: {embeddings[0 , :3]} {time.time() - t0:.2f}")

    # now for 4
    for i in range(0, len(SENTENCES), 4):
        sentence_pair = " ".join(SENTENCES[i:i + 4])
        t0 = time.time()
        embeddings = encoder.encode([sentence_pair])
        print(f"Sentence  : {sentence_pair[:30]}...{sentence_pair[-30:]} : "
              f"embeddings: {embeddings[0 , :3]} {time.time() - t0:.2f}")


if __name__ == "__main__":
    main()
