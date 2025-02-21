import random

from back_fastapi.algorithm import weather_fun, build_graph, find_top_n_paths
from back_fastapi.clothes_repository import ClothingsResponse

# Define categories and subcategories
val_categories = ["Shirts", "Layers", "Pants", "Shoes", "Accessories"]
val_subcategories = {
    "Shirts": ["T-Shirts", "Button-ups", "Polo-shirts"],
    "Layers": ["Sweaters", "Sweatshirts", "Jackets", "Cover ups", "Blazers"],
    "Pants": ["Jeans", "Sweatpants", "Shorts", "Dress trousers", "Chinos"],
    "Shoes": ["Sneakers", "Boots", "Oxfords", "Loafers", "Sandals"],
    "Accessories": ["Earrings", "Necklaces", "Rings", "Scarves", "Hats", "Bags", "Sunglasses", "Belts", "Bracelets",
                    "Face masks", "Watches"],
}

# Sample mock clothes data (with random attributes)
clothes = []


# Function to generate mock clothes
def generate_mock_clothes(num_items=100):
    item_id = 1
    for category in val_categories:
        for subcategory in val_subcategories[category]:
            for _ in range(num_items // len(val_categories)):  # Even distribution across categories
                warmness = random.choice(['Medium', 'Light', 'Extra light', 'Warm', 'Extra warm'])
                color = random.choice(["Red", "Blue", "Green", "Black", "White", "Yellow", "Purple", "Pink"])
                cloth = {
                    "id": item_id,
                    "category": category,
                    "subcategory": subcategory,
                    "color": color,
                    "warmness": warmness
                }
                # print(cloth)
                cr = ClothingsResponse(
                    id=cloth["id"],
                    name="Winter Jacket",  # Missing in your example, must be added
                    category=cloth["category"],
                    subcategory=cloth["subcategory"],
                    warmness=cloth["warmness"],
                    color=cloth["color"],
                    image_url=""
                )
                clothes.append(cr)
                item_id += 1
    return clothes


def get_recommendations(temperature, weight, wardrobe):
    warmness_class = weather_fun(temperature, weight)
    filtered_clothes = list(filter(lambda item: item.warmness == warmness_class, wardrobe))
    graph = build_graph(filtered_clothes)
    if temperature > 10:
        return find_top_n_paths(graph, wardrobe, ["Shirts", "Pants", "Shoes"], 5)
    else:
        return find_top_n_paths(graph, wardrobe, ["Shirts", "Pants", "Shoes", "Layers"], 5)


if __name__ == '__main__':
    # Create a mock wardrobe
    mock_wardrobe = generate_mock_clothes()
    temperature = 10  # °C
    weight = 75  # kg
    print(weather_fun(-15, 75))
    # paths = get_recommendations(temperature, weight, mock_wardrobe)
    # for path in paths:
    #     print(path)


# Display the mock wardrobe
# for cloth in mock_wardrobe:
#     print(f"ID: {cloth['id']}, Category: {cloth['category']}, Subcategory: {cloth['subcategory']}, Color: {cloth['color']}, Warmness: {cloth['warmness']}")
