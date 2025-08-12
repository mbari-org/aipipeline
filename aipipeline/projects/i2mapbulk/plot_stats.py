# Plot species with less than 50 examples
import matplotlib.pyplot as plt

# Data dictionary
data = {
    "Acanthamunnopsis milleri": 194, "Actinopterygii": 1888, "Aegina": 248, "Aegina citrea": 8,
    "Aegina rosea": 9, "Appendicularia": 168, "Atolla": 101, "Bargmannia": 1, "Bathochordaeus": 13,
    "Bathochordaeus sinker": 87, "Bathylagidae": 1, "Bathylagoides wesethi": 1, "Beroe": 111,
    "Caecosagitta macrocephala": 18, "Calycophorae": 85, "Chaetognatha": 447, "Chiroteuthis calyx": 49,
    "Chuniphyes": 91, "Colobonema sericeum": 5, "Copepoda": 28, "Cranchiidae": 4, "Ctenophora": 5,
    "Cyclosalpa": 29, "Cyclothone": 28, "Cydippida": 198, "Cydippida sp. A": 31, "Earleria corachloeae": 50,
    "Earleria pupurea": 3, "Euchirella bitumida": 35, "Eumedusa": 2, "Euphausiacea": 1892,
    "Euphysa": 7, "Eusergestes similis": 1613, "Eutonina indicans": 1, "Forskalia": 5, "Fritillariidae": 1,
    "Gonatus": 11, "Gymnopraia lapislazula": 87, "Haliscera conica": 103, "Hastigerinella digitata": 48,
    "Lensia": 69, "Lensia conoidea": 14, "Leuroglossus stilbius": 26, "Medusae": 119,
    "Melanostigma pammelas": 7, "Merluccius productus": 975, "Mitrocoma cellularia": 1,
    "Modeeria rotunda": 9, "Munnopsidae": 14, "Myctophidae": 27, "Mysida": 41, "Nanomia 2": 24,
    "Nanomia bijuga": 1431, "Octogonade mediterranea": 3, "Pantachogon": 13, "Pasiphaea": 106,
    "Periphylla": 3, "Periphylla periphylla": 10, "Poeobius meseres": 357, "Poralia rufescens": 1,
    "Procymbulia": 1, "Pyrosoma": 799, "Radiozoa": 61, "Redhead sinker": 3, "Rhopalonema": 2,
    "Sergestid molt": 15, "Sergestidae": 6, "Siphonophorae": 8, "Solmaris": 5, "Solmissus": 353,
    "Solmundella bitentaculata": 97, "Tomopteridae": 63, "Tuscaroridae": 45, "Vitreosalpa gemini": 603,
    "Vogtia": 1, "ink": 2, "krill molt": 536, "marine snow": 134, "sinker": 127, "Agalmatidae": 2,
    "Beroe cucumis": 1, "Bolinopsis": 10, "Crustacea": 38, "Cystisoma": 1, "Hormiphora californensis": 16,
    "Phronima": 2, "Physonectae": 13, "Resomia ornicephala": 4, "Salpa fusiformis": 4,
    "Teuthoidea": 16, "Thalassocalyce inconstans": 4, "Thalassocracy inconstans": 34, "Unknown": 2
}

# Sort data by values
sorted_data = dict(sorted(data.items(), key=lambda item: item[1]))

# Plot data
plt.figure(figsize=(12, 12))
plt.barh(list(sorted_data.keys()), list(sorted_data.values()), color="skyblue")
plt.xlabel("Count")
plt.ylabel("Species")
plt.title("Species Count in Ascending Order")
plt.yticks(rotation=20)
plt.show()


# Filter data for species with less than 50 examples
filtered_data = {k: v for k, v in sorted_data.items() if v < 50}

# Plot filtered data
plt.figure(figsize=(12, 12))
plt.barh(list(filtered_data.keys()), list(filtered_data.values()), color="lightcoral")
plt.xlabel("Count")
plt.ylabel("Species")
plt.title("Species with Less Than 50 Examples")
plt.yticks(rotation=20)
plt.show()
# Save the filtered data to a file
with open("filtered_data.txt", "w") as f:
    for k, v in filtered_data.items():
        f.write(f"{k}: {v}\n")