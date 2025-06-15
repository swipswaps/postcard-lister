import openai
import json
import base64
from openai import OpenAI

def image_to_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def read_value_list(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def get_postcard_metadata(combined_img_path: str, api_key: str) -> dict:
    client = OpenAI(api_key=api_key)

    # Load region and city lists
    region_list = read_value_list("data/region_values.txt")
    city_list = read_value_list("data/city_values.txt")
    subject_list = read_value_list("data/subject_values.txt")
    country_list = read_value_list("data/country_values.txt")
    theme_list = read_value_list("data/theme_values.txt")
    type_list = read_value_list("data/type_values.txt")
    era_list = read_value_list("data/era_values.txt")

    try:
        print(f"Processing image: {combined_img_path}")
        b64_image = image_to_base64(combined_img_path)
        print("Image converted to base64 successfully")

        # Construct fixed prompt
        system_message = (
            "You are a postcard expert that extracts structured metadata from postcard images for eBay listings. "
            "You are given a combined image of a postcard front and back. "
            "Please extract the following fields in JSON format: City, State, Country, Region, Year, Publisher, Era, Type, Subject, Theme, Title, Description, Posted"
            "If you cannot find a match, return nothing for that element, just an empty string."
            "For 'Region', choose the closest match from this list, if any:\n"
            f"{', '.join(region_list)}\n\n"
            "For 'City', choose the closest match from this list, if any:\n"
            f"{', '.join(city_list)}\n\n"
            "For 'Country', choose the closest match from this list, if any:\n"
            f"{', '.join(country_list)}\n\n"
            "For 'Subject', choose the closest match from this list, if any:\n"
            f"{', '.join(subject_list)}\n\n"
            "For 'Theme', choose the closest match from this list, if any:\n"
            f"{', '.join(theme_list)}\n\n"
            "For 'Type', choose the closest match from this list, if any:\n"
            f"{', '.join(type_list)}\n\n"
            "For 'Era', choose the closest match from this list, if any:\n"
            f"{', '.join(era_list)}\n\n",
            "For 'Title', please provide an eBay search engine optimized title to help the listing rank higher while accurately describing it. The title must be 80 characters in length maximum and should always include the word 'Postcard'. Use as many of those 80 characters as possible by using relevant keywords such as the subject, theme, city, state, and other terms collectors may be searching for. Do not repeat keywords in the title. Aim for a title that is at least 70 characters long but the closer to 80 the better. If you cannot fit 80 characters, do not exceed that limit.",
            "For 'Description', please provide a detailed description of the postcard. This should be a concise summary of the image, including the subject, theme, city, state, and other details. Use HTML to format the description into a paragraph (or paragraphs if necessary) for the eBay description.",
            "For 'Posted', choose either 'Posted' or 'Unposted'. If a postcard has a stamp on it and/or writing, it is Posted. If it is blank, it is Unposted. \n"
            "If there are people in the image you do NOT have to personally identify them. Just provide the required data."
        )

        print("Making API call to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{b64_image}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": "Please extract the metadata now."
                        }
                    ]
                }
            ],
            temperature=0.2,
            max_tokens=16384
        )
        print("API call completed successfully")

        raw = response.choices[0].message.content.strip()
        print(f"Raw response: {raw}")

        if raw.startswith("```"):
            raw = raw.split("```")[1].strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()

        result = json.loads(raw)
        print(f"Parsed JSON result: {result}")
        return result

    except Exception as e:
        print(f"⚠️ Failed to parse AI response: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {}
