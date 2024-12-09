from openai import OpenAI
client = OpenAI()

completion = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": (
                "should I tell my girlfriend we're over over text? "
                "I'm too scared to do it in person. I don't want to hurt her."
            )
        }
    ]
)

print(completion.choices[0].message.content)
