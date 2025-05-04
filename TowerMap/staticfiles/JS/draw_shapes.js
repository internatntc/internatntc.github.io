window.towersInRegion = [];

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

    async function displaySelectedTowers() {
        const towerInfo = document.getElementById("towerInfo");
        if (!towerInfo) return;

        // Fetch all towers if not already loaded
        if (allTowers.length === 0) {
            const response = await fetch('/map/get-towers/');
            const data = await response.json();
            allTowers = data.towers;
        }

        // When no polygons are drawn, show towers from the selected GeoJSON area
        if (drawnItems.getLayers().length === 0) {
            // When no drawn polygons, display towers from the selected GeoJSON area
            displayTowers(selectedGeojsonTowers, true);  // Show previously selected towers on map
            return;
        }

        const selectedTowers = new Set();

        drawnItems.getLayers().forEach(layer => {
            selectedGeojsonTowers.forEach(tower => {
                const towerPoint = turf.point([tower.longitude, tower.latitude]);
                if (isPointInShape([tower.longitude, tower.latitude], layer)) {
                    selectedTowers.add(tower);
                }
            });
        });

        // Update towerInfo with the selected towers inside the drawn polygons
        displayTowers([...selectedTowers], false);  // Don't update the map, just the info panel
    }


    window.map.on("draw:created", (e) => {
        drawnItems.addLayer(e.layer);
        displaySelectedTowers();
    });

    window.map.on("draw:edited", () => {
        displaySelectedTowers();
    });

    window.map.on("draw:deleted", () => {
        displaySelectedTowers();
    });
    window.map.on('layerremove', (event) => {
        if (event.layer === drawnItems) {
            displayTowers(selectedGeojsonTowers, true);  // Show the selected GeoJSON towers
        }
    });
});
