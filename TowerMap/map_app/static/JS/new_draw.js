document.addEventListener("DOMContentLoaded", function () {
    const drawnItems = new L.FeatureGroup();
    window.map.addLayer(drawnItems);

    const drawControl = new L.Control.Draw({
        edit: { featureGroup: drawnItems },
        draw: {
            polygon: true,
            rectangle: true,
            circle: true,
            marker: false,
            polyline: false,
        },
    });

    window.map.addControl(drawControl);

    function isPointInShape(point, layer) {
        if (layer instanceof L.Circle) {
            const center = layer.getLatLng();
            const radius = layer.getRadius();
            const points = 64;
            const coords = [];

            for (let i = 0; i < points; i++) {
                const angle = (i / points) * (2 * Math.PI);
                const lat = center.lat + (radius / 111319) * Math.sin(angle);
                const lng = center.lng + (radius / (111319 * Math.cos(center.lat * (Math.PI / 180)))) * Math.cos(angle);
                coords.push([lng, lat]);
            }
            coords.push(coords[0]);

            const circleAsPolygon = {
                type: "Feature",
                properties: {},
                geometry: {
                    type: "Polygon",
                    coordinates: [coords]
                }
            };
            return turf.booleanPointInPolygon(turf.point(point), circleAsPolygon);
        } else {
            const shapeGeoJSON = layer.toGeoJSON();
            return turf.booleanPointInPolygon(turf.point(point), shapeGeoJSON);
        }
    }

    async function handleDrawnShapes() {
        const towerInfo = document.getElementById("towerInfo");
        if (!towerInfo) return;

        // When no polygons are drawn, clear the displayed towers
        if (drawnItems.getLayers().length === 0) {
            window.towersInRegion = [];
            displayTowers([], true);
            return;
        }

        // Get combined bounding box of all drawn layers
        const layersGeoJSON = {
            type: "FeatureCollection",
            features: drawnItems.getLayers().map(layer => layer.toGeoJSON())
        };
        const bbox = turf.bbox(layersGeoJSON);

        try {
            // Fetch towers within the bounding box
            const response = await fetch(`/map/get-towers/?bbox=${bbox.join(',')}`);
            const data = await response.json();
            const towersInBbox = data.towers;

            // Precisely filter towers using Turf.js
            const selectedTowers = [];
            drawnItems.getLayers().forEach(layer => {
                towersInBbox.forEach(tower => {
                    if (isPointInShape([tower.longitude, tower.latitude], layer)) {
                        selectedTowers.push(tower);
                    }
                });
            });

            // Remove duplicates and update display
            window.towersInRegion = [...new Set(selectedTowers)];
            displayTowers(window.towersInRegion, true);
        } catch (error) {
            console.error("Error fetching towers:", error);
        }
    }

    // Clear all drawn shapes and reset towers
    function clearAllShapes() {
        drawnItems.clearLayers();
        window.towersInRegion = [];
        displayTowers([], true);
    }

    // Event handlers
    window.map.on("draw:created", (e) => {
        drawnItems.addLayer(e.layer);
        handleDrawnShapes();
    });

    window.map.on("draw:edited", handleDrawnShapes);

    window.map.on("draw:deleted", function (e) {
        // Check if all layers were deleted
        if (drawnItems.getLayers().length === 0) {
            clearAllShapes();
        } else {
            handleDrawnShapes();
        }
    });

    // Add clear button handler if you have one
    document.getElementById('clearShapesBtn')?.addEventListener('click', clearAllShapes);

    window.map.on('layerremove', (event) => {
        //     if (event.layer === drawnItems) {
        //         displayTowers(selectedGeojsonTowers, true);
        //         window.towersInRegion = selectedGeojsonTowers;
        //     }
        // });
        if (event.layer === drawnItems) {
            displayTowers(selectedGeojsonTowers, true);  // Show the selected GeoJSON towers
        }
    });
});