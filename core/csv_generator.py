import pandas as pd
import copy

def load_template(template_path: str) -> pd.DataFrame:
    return pd.read_csv(template_path)

def fill_row(headers: list[str], metadata: dict, front_url: str, back_url: str, combined_url: str, folder_label: str, settings: dict) -> pd.Series:
    row = {header: "" for header in headers}
    
    row['*Action(SiteID=US|Country=US|Currency=USD|Version=1193)'] = "Add"
    from datetime import datetime, timedelta
    today_str = datetime.today().strftime('%Y-%m-%d')
    row['Custom label (SKU)'] = f"{folder_label} - {today_str}"
    row['Title'] = metadata.get('Title', '')
    future_date = datetime.now() + timedelta(days=1)
    row['Schedule Time'] = future_date.strftime("%Y-%m-%d") + " 18:00:00"
    row['Item photo URL'] = f"{front_url}|{back_url}|{combined_url}|https://pcc-ebay-photos.s3.us-east-1.amazonaws.com/PCC-banner.png"
    row['Category ID'] = "262042"
    row['Condition ID'] = "3000-Used"
    row['Category name'] = '/Collectibles/Postcards & Supplies/Postcards/Topographical Postcards'
    row['Start price'] = "8.99"
    row['Quantity'] = 1
    row['Format'] = "FixedPrice"
    row['Duration'] = "GTC"
    row['Best Offer Enabled'] = "1"
    row['Location'] = settings.get('zip_code', '')
    row['Shipping profile name'] = settings.get('shipping_policy', '')
    row['Return profile name'] = settings.get('return_policy', '')
    row['Payment profile name'] = settings.get('payment_policy', '')
    row['C:Unit of Sale'] = "Single Unit"
    row['C:Region'] = metadata.get("Region", '')
    row['C:City'] = metadata.get("City", '')
    row['C:Subject'] = metadata.get("Subject", '')
    row['C:Country'] = metadata.get("Country", '')
    row['C:Country/Region of Manufacture'] = ""
    row['C:Original/Licensed Reprint'] = "Original"
    row['C:Theme'] = metadata.get("Theme", '')
    row['C:Type'] = metadata.get("Type", '')
    row['C:Posted Condition'] = metadata.get("Posted Condition", '')
    row['C:Era'] = metadata.get("Era", '')
    row['Store category'] = "4231764019"
    row['Description'] = f"<h1>{metadata.get('Title', '')}</h1><br><p>You will receive the exact postcard in the scans. Please view the scans and message me if you have any questions because I can usually respond within minutes.</p><br>{metadata.get('Description', '')}{settings.get('custom_html', '').format(**metadata)}"

    return pd.Series(row)

def generate_csv(output_path: str, template_path: str, all_rows: list):
    template = pd.read_csv(template_path)
    headers = list(template.columns)

    df = pd.DataFrame([fill_row(headers, *row_data) for row_data in all_rows])
    df.to_csv(output_path, index=False)
    return output_path