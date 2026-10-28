const fs = require('fs');

// Seeded random generator makes this sample dataset repeatable.
let seed = 20260930;
function random() {
    seed = (seed * 1664525 + 1013904223) % 4294967296;
    return seed / 4294967296;
}
function pick(list) { return list[Math.floor(random() * list.length)]; }
function number(min, max) { return Math.floor(random() * (max - min + 1)) + min; }
function csvValue(value) { return '"' + String(value ?? '').replace(/"/g, '""') + '"'; }

const brands = ['Aurora Bloom', 'Velvet Leaf', 'Luma Skin', 'Pure Petal', 'Glow Theory', 'Nectar & Co', 'Mira Botanics', 'Clover Cosmetics'];
const catalog = [
    ['Skincare', 'Cleanser', 'Daily Cleanser'], ['Skincare', 'Serum', 'Radiance Serum'], ['Skincare', 'Moisturizer', 'Cloud Cream'],
    ['Skincare', 'Sunscreen', 'Sun Shield'], ['Makeup', 'Foundation', 'Soft Matte Foundation'], ['Makeup', 'Lipstick', 'Velvet Lip Color'],
    ['Makeup', 'Mascara', 'Lift Mascara'], ['Makeup', 'Blush', 'Silk Blush'], ['Haircare', 'Shampoo', 'Repair Shampoo'],
    ['Haircare', 'Conditioner', 'Smooth Conditioner'], ['Haircare', 'Hair Oil', 'Nourishing Hair Oil'], ['Fragrance', 'Perfume', 'Eau de Parfum'],
    ['Fragrance', 'Body Mist', 'Fresh Body Mist'], ['Bath & Body', 'Body Lotion', 'Hydrating Body Lotion'], ['Bath & Body', 'Body Wash', 'Gentle Body Wash']
];
const ingredients = ['Hyaluronic Acid', 'Niacinamide', 'Vitamin C', 'Aloe Vera', 'Shea Butter', 'Rose Extract', 'Ceramides', 'Green Tea'];
const shades = ['Rose', 'Nude', 'Berry', 'Honey', 'Ivory', 'Peach', 'Vanilla', 'Unscented'];
const countries = ['India', 'South Korea', 'France', 'Japan', 'United States'];
const rows = [[
    'Product_ID', 'Product_Name', 'Brand', 'Category', 'Subcategory', 'Skin_Type', 'Shade_or_Scent', 'Price_INR',
    'Discount_Percent', 'Rating', 'Review_Count', 'Stock_Quantity', 'Units_Sold', 'Launch_Date', 'Country',
    'Is_Vegan', 'Is_Cruelty_Free', 'Expiry_Months', 'Key_Ingredient', 'Customer_Segment'
]];

for (let index = 1; index <= 5000; index++) {
    const item = pick(catalog);
    const price = number(199, 2999);
    const month = String(number(1, 12)).padStart(2, '0');
    const day = String(number(1, 28)).padStart(2, '0');
    rows.push([
        `BP${String(index).padStart(5, '0')}`,
        `${pick(['Essential', 'Signature', 'Advanced', 'Gentle', 'Daily'])} ${item[2]} ${number(1, 99)}`,
        pick(brands), item[0], item[1], pick(['Dry', 'Normal', 'Oily', 'Combination', 'Sensitive']), pick(shades), price,
        pick([0, 5, 10, 15, 20, 25, 30]), random() < 0.035 ? '' : (3.4 + random() * 1.6).toFixed(1), number(5, 2400),
        number(0, 900), number(5, 12000), `${number(2021, 2026)}-${month}-${day}`, pick(countries),
        pick(['Yes', 'No']), pick(['Yes', 'No']), pick([12, 18, 24, 36]), random() < 0.04 ? '' : pick(ingredients),
        pick(['Student', 'Young Adult', 'Working Professional', 'Family', 'Premium Shopper'])
    ]);
}

// Add a few intentional duplicate records to test the cleaning page.
for (let index = 1; index <= 25; index++) rows.push([...rows[index]]);

const content = rows.map(row => row.map(csvValue).join(',')).join('\n');
fs.writeFileSync('sample_data/beauty_products_5000.csv', content, 'utf8');
console.log(`Created ${rows.length - 1} data rows in sample_data/beauty_products_5000.csv`);
