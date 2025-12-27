# Improvement: Vision Model for Species Identification

**Category**: Improvement
**Task ID**: imp-5
**Status**: TODO
**Started**: Not started
**Completed**: Not completed
**Priority**: Medium

## Description

Research and evaluate vision models for improved outdoor species identification.
The current MobileNetV3 (ImageNet-1000) model has limited accuracy for plants,
mushrooms, and wildlife because ImageNet has minimal species-specific coverage.

## Current State

- MobileNetV3 Small trained on ImageNet-1000 with generic classes
- Limited species coverage (~10 mushroom types, few wildlife species)
- Low confidence (0-20%) on outdoor photos
- No safety information for dangerous species

## Goals

1. Find a TFLite-compatible model trained on nature/species data
2. Model should be <100MB and run on Raspberry Pi 5 (<500ms inference)
3. Cover common outdoor species: plants, fungi, wildlife
4. Include or support safety warnings for dangerous species

## Research Tasks

- [ ] Survey HuggingFace for iNaturalist or nature-trained TFLite models
- [ ] Evaluate timm library models with iNaturalist weights
- [ ] Research PlantNet, FungiCLEF, and similar open-source projects
- [ ] Test BioCLIP or MobileCLIP for zero-shot species classification
- [ ] Benchmark promising models on Pi 5 for latency and accuracy
- [ ] Document findings and recommended approach

## HuggingFace Models to Investigate

| Model | Source | Notes |
|-------|--------|-------|
| timm/efficientnet_* | HuggingFace | May have iNat pretrained versions |
| google/vit-* | HuggingFace | Vision transformers, may be too large |
| apple/MobileCLIP | HuggingFace | Zero-shot, ~150MB |
| BioCLIP | OpenCLIP | Trained on biology images |

## Open Source Projects to Research

| Project | URL | Notes |
|---------|-----|-------|
| iNaturalist | github.com/visipedia/inat_comp | Official competition models |
| PlantNet | plantnet.org | Plant identification API/models |
| FungiCLEF | imageclef.org/FungiCLEF | Mushroom classification |
| BirdNET | github.com/kahst/BirdNET-Analyzer | Bird identification |

## Acceptance Criteria

- [ ] Document at least 3 candidate models with pros/cons
- [ ] Benchmark at least 1 model on Pi 5 for latency
- [ ] Provide recommendation for implementation approach
- [ ] Estimate effort for integration

## Notes

This task focuses on research and evaluation. Implementation will be a separate
task once a suitable model is identified.

## Resources

- iNaturalist models: https://github.com/visipedia/inat_comp
- timm library: https://github.com/huggingface/pytorch-image-models
- TFLite Model Maker: https://www.tensorflow.org/lite/models/modify/model_maker
- BioCLIP: https://github.com/Imageomics/BioCLIP
