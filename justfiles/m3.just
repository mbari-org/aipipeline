# Copy m3 dev code to the project on doris
cp-dev-m3:
    #!/usr/bin/env bash
    cd ..
    cp justfiles/m3.just /Volumes/dcline/code/aipipeline/justfiles/m3.just
    rsync -rtv --no-group --exclude='*.DS_Store' --exclude='*.log' --exclude='*__pycache__' aipipeline/projects/m3/ /Volumes/dcline/code/aipipeline/aipipeline/projects/m3/

# Initiailize the VSS database with M3 transect data. Run after crop-m3-transect
init-m3-vss:
    #!/usr/bin/env bash
    export PROJECT_DIR=./aipipeline/projects/m3
    export PYTHONPATH=.
    time conda run -n aipipeline --no-capture-output python3 aipipeline/projects/m3/init_vss_pipeline.py\
          --config $PROJECT_DIR/config/config.yml \
          --input /mnt/ML_SCRATCH/m3/crops \
          --clean

# Crop M3 transect data to 224x224. Run after download-m3-transect
crop-m3-transect:
    # !/usr/bin/env bash
    time docker run -it \
    --rm -u $(id -u):$(id -g) \
    -v /mnt/ML_SCRATCH/m3:/mnt/ML_SCRATCH/m3 mbari/voc-imagecropper \
    -d /mnt/ML_SCRATCH/m3/xml/ \
    --resize 224x224 \
    --image_dir /mnt/ML_SCRATCH/m3/images/ \
    -o /mnt/ML_SCRATCH/m3/crops/

# Download M3 transect data
download-m3-transect:
    m3-download generate --config-url https://m3.shore.mbari.org/config \
    --exclude-activity "ascend" --exclude-activity "descend"  --exclude-activity "cruise"  \
    --exclude-activity "cruise"  --exclude-activity "stationary" \
    --exclude-activity "launch" --exclude-activity "off transect" --exclude-activity "topo" \
    --exclude-activity "unspecified"  --exclude-activity "possible duplicate" \
    --exclude-activity "localize" \
    --include-concept "Acanthamunnopsis milleri" --include-concept "Actinopterygii" --include-concept "Aegina" \
    --include-concept "Aegina citrea" --include-concept "Aegina rosea" --include-concept "Appendicularia" \
    --include-concept "Atolla" --include-concept "Bathochordaeus" --include-concept "Bathochordaeus sinker" \
    --include-concept "Beroe" --include-concept "Bolinopsis" --include-concept "Caecosagitta macrocephala" \
    --include-concept "Calycophorae" --include-concept "Chaetognatha" --include-concept "Chiroteuthis calyx" \
    --include-concept "Chuniphyes" --include-concept "Colobonema sericeum" --include-concept "Copepoda" \
    --include-concept "Crustacea" --include-concept "Ctenophora" --include-concept "Cyclosalpa" \
    --include-concept "Cyclothone" --include-concept "Cydippida" --include-concept "Cydippida sp. A" \
    --include-concept "Earleria corachloeae" --include-concept "Earleria pupurea" --include-concept "Euchirella bitumida" \
    --include-concept "Eumedusa" --include-concept "Euphausiacea" --include-concept "Eusergestes similis" \
    --include-concept "Eutonina indicans" --include-concept "Forskalia" --include-concept "Gonatus" \
    --include-concept "Gymnopraia lapislazula" --include-concept "Haliscera conica" \
    --include-concept "Hastigerinella digitata" --include-concept "Lensia" --include-concept "Lensia conoidea" \
    --include-concept "Leuroglossus stilbius" --include-concept "Medusae" --include-concept "Melanostigma pammelas" \
    --include-concept "Merluccius productus" --include-concept "Mitrocoma cellularia" --include-concept "Modeeria rotunda" \
    --include-concept "Munnopsidae" --include-concept "Myctophidae" --include-concept "Mysida" --include-concept "Nanomia 2" \
    --include-concept "Nanomia bijuga" --include-concept "Octogonade mediterranea" --include-concept "Pantachogon" \
    --include-concept "Pasiphaea" --include-concept "Periphylla" --include-concept "Periphylla periphylla" \
    --include-concept "Physophora" --include-concept "Poeobius meseres" --include-concept "Poralia rufescens" \
    --include-concept "Procymbulia" --include-concept "Pyrosoma" --include-concept "Radiozoa" --include-concept "Redhead sinker" \
    --include-concept "Rhopalonema" --include-concept "Salpa fusiformis" --include-concept "Salpidae" --include-concept "Sergestidae" \
    --include-concept "Siphonophorae" --include-concept "Solmaris" --include-concept "Solmissus" \
    --include-concept "Solmundella bitentaculata" --include-concept "Thalassocalyce inconstans" \
    --include-concept "Thalassocracy inconstans" --include-concept "Tomopteridae" --include-concept "Tuscaroridae" \
    --include-concept "Vitreosalpa gemini" --include-concept "Vogtia" --include-concept "ink" \
    --include-concept "krill molt" --include-concept "sinker" \
    /mnt/ML_SCRATCH/m3/images/ /mnt/ML_SCRATCH/m3/xml/