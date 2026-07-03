from voynich.acquisition.yale import (
    child_oid_from_service,
    normalize_manifest,
    text_value,
)


def test_text_value_handles_iiif_v3_language_map() -> None:
    assert text_value({"none": ["f1r"]}) == "f1r"


def test_child_oid_is_observational_identifier_only() -> None:
    assert child_oid_from_service("https://collections.library.yale.edu/iiif/2/1006001") == "1006001"
    assert child_oid_from_service("https://example.org/not-numeric") is None


def test_normalize_v3_manifest() -> None:
    manifest = {
        "id": "https://example.org/manifest.json",
        "type": "Manifest",
        "items": [
            {
                "id": "https://example.org/canvas/1",
                "type": "Canvas",
                "label": {"none": ["folio label retained verbatim"]},
                "width": 1200,
                "height": 1600,
                "items": [
                    {
                        "type": "AnnotationPage",
                        "items": [
                            {
                                "type": "Annotation",
                                "body": {
                                    "id": "https://example.org/iiif/2/1006001/full/full/0/default.jpg",
                                    "type": "Image",
                                    "service": [
                                        {
                                            "@id": "https://example.org/iiif/2/1006001",
                                            "@type": "ImageService2",
                                        }
                                    ],
                                },
                            }
                        ],
                    }
                ],
            }
        ],
    }
    records = normalize_manifest(manifest, "https://example.org/manifest.json")
    assert len(records) == 1
    assert records[0].sequence_index == 1
    assert records[0].label == "folio label retained verbatim"
    assert records[0].child_oid == "1006001"
    assert records[0].width_px == 1200
    assert records[0].height_px == 1600
    assert records[0].image_info_url.endswith("/1006001/info.json")


def test_normalize_v2_manifest() -> None:
    manifest = {
        "@id": "https://example.org/manifest.json",
        "@type": "sc:Manifest",
        "sequences": [
            {
                "canvases": [
                    {
                        "@id": "https://example.org/canvas/2",
                        "label": "page two",
                        "width": 800,
                        "height": 900,
                        "images": [
                            {
                                "resource": {
                                    "@id": "https://example.org/iiif/2/1006002/full/full/0/default.jpg",
                                    "service": {
                                        "@id": "https://example.org/iiif/2/1006002"
                                    },
                                }
                            }
                        ],
                    }
                ]
            }
        ],
    }
    records = normalize_manifest(manifest, "https://example.org/manifest.json")
    assert records[0].child_oid == "1006002"
    assert records[0].label == "page two"
