# PubMed-Image-Caption

Command Line Usage Example:

## Basic Command
  Fetch articles related to "histopathology" with a maximum of 10 results:

```
   python pubmed_images_caption.py --term histopathology --retmax 10
```

## Custom Search Term and Result Count
   Search for "cancer biomarkers" with a maximum of 50 results:  
```
   python pubmed_images_caption.py --term cancer biomarkers --retmax 50
```

## Output Naming
   The output file will be saved with the name format:  
```
<search_term>_<retmax>_<timestamp>.json
```
   Example output for the first command:  
   histopathology_10_20231225_123456.json
