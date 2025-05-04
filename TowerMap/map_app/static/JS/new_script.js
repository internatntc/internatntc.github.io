
document.addEventListener("DOMContentLoaded", function () {
    window.map = L.map('map').setView([28.3949, 84.1240], 7);
    consttiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '© OpenStreetMap'
    }).addTo(map);


    let nepalLayer;
    let provinceLayer;
    let districtLayer;
    let municipalityLayer;
    let wardLayer;
    let towerLayer;
    let allDistricts = null;
    let allMunicipalities = null;
    let allWards = null;
    window.allTowers = [];
    window.displayTowers = displayTowers;  // Expose function globally
    window.displayedTowers = [];  // Store currently displayed towers
    window.selectedGeojsonTowers = [];  // Store towers from the selected GeoJSON area

    // async function loadTowers() {
    //     const response = await fetch('/map/get-towers/');
    //     const data = await response.json();
    //     allTowers = data.towers;
    // }
    // loadTowers();

    // Keeps track of the towers shown on the map
    async function displayTowers(filteredTowers = [], updateMap = null) {
        const towerInfo = document.getElementById('towerInfo');
        const towerHeader = document.getElementById('towerHeader');
        const selectAllBtn = document.getElementById('selectAllBtn');
        const deselectAllBtn = document.getElementById('deselectAllBtn');

        // Determine which towers to show
        const towersToShow = filteredTowers.length > 0 ? filteredTowers :
            window.towersInRegion.length > 0 ? window.towersInRegion :
                selectedGeojsonTowers;

        // Update tower count in the header
        towerHeader.innerHTML = `<i class="bi bi-broadcast-pin me-2"></i> Registered Towers (${towersToShow.length}) `;

        // Toggle UI elements based on whether we have towers
        if (towersToShow.length === 0) {
            towerInfo.style.display = "none";
            if (selectAllBtn) selectAllBtn.style.display = "none";
            if (deselectAllBtn) deselectAllBtn.style.display = "none";
            return;
        } else {
            towerInfo.style.display = "grid";
            if (selectAllBtn) selectAllBtn.style.display = "inline-block";
            if (deselectAllBtn) deselectAllBtn.style.display = "inline-block";
        }

        // Clear previous content
        towerInfo.innerHTML = "";

        // Apply grid layout
        towerInfo.style.display = "grid";
        towerInfo.style.gridTemplateColumns = "repeat(auto-fill, minmax(150px, 1fr))";
        towerInfo.style.columnGap = "50px";
        towerInfo.style.rowGap = "10px";
        towerInfo.style.padding = "10px";

        // Add towers to the display
        towersToShow.forEach(tower => {
            const container = document.createElement('div');
            container.className = "form-check form-switch tower-item";

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'form-check-input';
            checkbox.id = `tower-${tower.id}`;
            checkbox.checked = true;
            checkbox.value = tower.id;

            const label = document.createElement('label');
            label.className = 'form-check-label';
            label.htmlFor = `tower-${tower.id}`;
            label.innerText = ` ${tower.name}`;

            container.appendChild(checkbox);
            container.appendChild(label);
            towerInfo.appendChild(container);
        });

        // Update map if requested
        if (updateMap) {
            updateMapTowers(towersToShow);
        }

        // Set up button handlers
        if (selectAllBtn) {
            selectAllBtn.onclick = () => {
                document.querySelectorAll("#towerInfo input[type='checkbox']").forEach(checkbox => {
                    checkbox.checked = true;
                });
            };
        }

        if (deselectAllBtn) {
            deselectAllBtn.onclick = () => {
                document.querySelectorAll("#towerInfo input[type='checkbox']").forEach(checkbox => {
                    checkbox.checked = false;
                });
            };
        }
    }


    function updateMapTowers(towers) {
        if (towerLayer) {
            map.removeLayer(towerLayer);
        }

        let markers = towers.map(tower => {
            return L.marker([tower.latitude, tower.longitude], {
                icon: L.icon({
                    iconUrl: '/static/Images/tower_2.png',
                    iconSize: [12, 26],
                    iconAnchor: [6, 26],
                    popupAnchor: [0, -26]
                })
            }).bindTooltip(`<strong>${tower.name}</strong>`);
        });
        // let markers = towers.map(tower => {
        //     return L.circleMarker([tower.latitude, tower.longitude], {
        //         radius: 1.5,            // Size of the marker
        //         color: "blue",
        //         fillColor: "#ff0000", // Fill color (Red)
        //         fillOpacity: 0.8
        //     }).bindTooltip(`<strong>${tower.name}</strong>`);
        // });
        towerLayer = L.layerGroup(markers).addTo(map);
        displayedTowers = towers; // Store currently displayed towers
    }

    // Modify your filterTowers function to handle GeoJSON polygons properly
    async function filterTowers(selectedFeature) {
        if (!selectedFeature) {
            // Clear towers if no area selected
            selectedGeojsonTowers = [];
            if (towerLayer) map.removeLayer(towerLayer);
            displayTowers([], true);
            return;
        }

        showLoadingModal();

        try {
            // Extract polygon coordinates from GeoJSON
            const coordinates = selectedFeature.geometry.coordinates;

            // Fetch ONLY towers within this polygon
            const response = await fetch('/map/get-towers/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken'),
                },
                body: JSON.stringify({
                    polygon: coordinates  // Send raw polygon coordinates
                })
            });

            const data = await response.json();
            selectedGeojsonTowers = data.towers;
            displayTowers(selectedGeojsonTowers, true);
        } catch (error) {
            console.error('Error fetching towers:', error);
            selectedGeojsonTowers = [];
            displayTowers([], true);
        } finally {
            hideLoadingModal();
        }
    }
    // Load all data first
    Promise.all([
        fetch('/static/JSON/Nepal_.geojson').then(res => res.json()),
        fetch('/static/JSON/provinces.geojson').then(res => res.json()),
        fetch('/static/JSON/districts.geojson').then(res => res.json()),
        fetch('/static/JSON/municipalities.geojson').then(res => res.json()),
        fetch('/static/JSON/wards.geojson').then(res => res.json()),

    ]).then(([nepalData, provincesData, districtsData, municipalitiesData, wardsData]) => {
        allDistricts = districtsData;
        allMunicipalities = municipalitiesData;
        allWards = wardsData;

        // Load nepal layer
        nepalLayer = L.geoJSON(nepalData, {
            style: feature => ({
                color: '#F6AE2D', weight: 2, fillOpacity: 0.1
            }),
            onEachFeature: (feature, layer) => {
                if (feature.properties) {
                    // Detailed tooltip with additional properties
                    const tooltipContent = `
                            <strong>${feature.properties['name:en'] || feature.properties['name']}</strong><br>
                            <strong>Nepali Name: ${feature.properties['name:ne'] || 'N/A'}</strong><br>
                            
                        `;
                    layer.bindTooltip(tooltipContent, { sticky: true });
                }
            }
        }).addTo(map);
        const Nepal = nepalData.features.find(f => f.properties["name"] === "नेपाल");
        console.log(Nepal);
        if (Nepal) {
            selectedGeojsonTowers = [];
            filterTowers(Nepal);
        }



        // Setup province dropdown
        const provinceDropdown = document.getElementById('provinceDropdown');
        provinceDropdown.innerHTML = '<option value="">Select a province</option>';
        provincesData.features.forEach(feature => {
            const name = feature.properties['name'];
            const option = document.createElement('option');
            option.value = name;
            option.textContent = feature.properties['name:en'];
            provinceDropdown.appendChild(option);
        });

        // Province dropdown change event
        provinceDropdown.addEventListener('change', function (e) {
            const districtDropdown = document.getElementById('districtDropdown');
            const municipalityDropdown = document.getElementById('municipalityDropdown');
            const wardDropdown = document.getElementById('wardDropdown');

            districtDropdown.innerHTML = '<option value="">Select a district</option>';
            municipalityDropdown.innerHTML = '<option value="">Select a district first</option>';
            wardDropdown.innerHTML = '<option value="">Select municipality first</option>';
            districtDropdown.disabled = true;
            municipalityDropdown.disabled = true;
            wardDropdown.disabled = true;

            if (provinceLayer) map.removeLayer(provinceLayer);
            if (districtLayer) map.removeLayer(districtLayer);
            if (municipalityLayer) map.removeLayer(municipalityLayer);
            if (wardLayer) map.removeLayer(wardLayer);

            const selectedName = e.target.value;
            if (selectedName) {
                const selectedProvince = provincesData.features.find(f => f.properties['name'] === selectedName);
                provinceLayer = L.geoJSON(selectedProvince, {
                    style: feature => ({
                        color: '#47682C', weight: 2, fillOpacity: 0.1
                    }),
                    onEachFeature: (feature, layer) => {
                        if (feature.properties) {
                            // Detailed tooltip with additional properties
                            const tooltipContent = `
                            <strong>${feature.properties['name:en'] || feature.properties['name']}</strong><br>
                           
                            <strong>Nepali Name: ${feature.properties['name:ne'] || 'N/A'}</strong><br>
                            
                        `;
                            layer.bindTooltip(tooltipContent, { sticky: true });
                        }
                    }
                }).addTo(map);
                map.fitBounds(provinceLayer.getBounds());
                updateDistrictDropdown(selectedProvince);
                filterTowers(null);
                districtDropdown.disabled = false;
            } else {

                if (nepalLayer) map.addLayer(nepalLayer);
                map.fitBounds(nepalLayer.getBounds());
            }
        });

        // Setup district dropdown change event
        function updateDistrictDropdown(provinceFeature) {
            const districtDropdown = document.getElementById('districtDropdown');
            districtDropdown.innerHTML = '<option value="">Select a district</option>';

            const provinceGeometry = turf.flatten(provinceFeature.geometry);

            allDistricts.features.forEach(districtFeature => {
                try {
                    const districtGeometry = turf.flatten(districtFeature.geometry);
                    const isContained = provinceGeometry.features.some(parentPart =>
                        districtGeometry.features.some(childPart =>
                            turf.booleanContains(parentPart, childPart)
                        )
                    );

                    if (isContained) {
                        const option = document.createElement('option');
                        option.value = districtFeature.properties['name'];
                        option.textContent = districtFeature.properties['name:en'];
                        districtDropdown.appendChild(option);
                    }
                } catch (e) {
                    console.error('District containment error:', e);
                }
            });

            districtDropdown.addEventListener('change', function (e) {
                const municipalityDropdown = document.getElementById('municipalityDropdown');
                const wardDropdown = document.getElementById('wardDropdown');
                municipalityDropdown.innerHTML = '<option value="">Select a municipality</option>';
                wardDropdown.innerHTML = '<option value="">Select municipality first</option>';
                municipalityDropdown.disabled = true;
                wardDropdown.disabled = true;

                if (districtLayer) map.removeLayer(districtLayer);
                if (municipalityLayer) map.removeLayer(municipalityLayer);
                if (wardLayer) map.removeLayer(wardLayer);


                const selectedDistrictName = e.target.value;
                if (selectedDistrictName) {
                    const selectedDistrict = allDistricts.features.find(
                        f => f.properties['name'] === selectedDistrictName
                    );
                    districtLayer = L.geoJSON(selectedDistrict, {
                        style: feature => ({
                            color: '#F26419', weight: 2, fillOpacity: 0.1
                        }),
                        onEachFeature: (feature, layer) => {
                            if (feature.properties) {
                                // Detailed tooltip with additional properties
                                const tooltipContent = `
                            <strong>${feature.properties['name:en'] || feature.properties['name']}</strong><br>
                            
                            <strong>Nepali Name: ${feature.properties['name:ne'] || 'N/A'}</strong><br>
                            
                        `;
                                layer.bindTooltip(tooltipContent, { sticky: true });
                            }
                        }
                    }).addTo(map);
                    map.fitBounds(districtLayer.getBounds());
                    updateMunicipalityDropdown(selectedDistrict);
                    filterTowers(selectedDistrict);
                    municipalityDropdown.disabled = false;
                }
            });
        }

        function updateMunicipalityDropdown(districtFeature) {
            const municipalityDropdown = document.getElementById('municipalityDropdown');
            municipalityDropdown.innerHTML = '<option value="">Select a municipality</option>';

            const districtGeometry = turf.flatten(districtFeature.geometry);

            allMunicipalities.features.forEach(municipalityFeature => {
                try {
                    const municipalityGeometry = turf.flatten(municipalityFeature.geometry);
                    const isContained = districtGeometry.features.some(parentPart =>
                        municipalityGeometry.features.some(childPart =>
                            turf.booleanContains(parentPart, childPart)
                        )
                    );

                    if (isContained) {
                        const option = document.createElement('option');
                        option.value = municipalityFeature.properties.name;
                        option.textContent = municipalityFeature.properties['name:en'] || municipalityFeature.properties['name'];
                        municipalityDropdown.appendChild(option);
                    }
                } catch (e) {
                    console.error('Municipality containment error:', e);
                }
            });

            municipalityDropdown.addEventListener('change', function (e) {
                const wardDropdown = document.getElementById('wardDropdown');
                wardDropdown.innerHTML = '<option value="">Select a ward</option>';
                wardDropdown.disabled = true;

                if (municipalityLayer) map.removeLayer(municipalityLayer);
                if (wardLayer) map.removeLayer(wardLayer);

                const selectedMunicipalityName = e.target.value;
                if (selectedMunicipalityName) {
                    const selectedMunicipality = allMunicipalities.features.find(
                        f => f.properties.name === selectedMunicipalityName
                    );
                    municipalityLayer = L.geoJSON(selectedMunicipality, {
                        style: feature => ({
                            color: '#118AB2', weight: 2, fillOpacity: 0.1
                        }),
                        onEachFeature: (feature, layer) => {
                            if (feature.properties) {
                                // Detailed tooltip with additional properties
                                const tooltipContent = `
                            <strong>${feature.properties['name:en'] || feature.properties['name']}</strong><br>
                              <strong>[${feature.properties['name:suffix']}]</strong><br>
                            
                            
                        `;
                                layer.bindTooltip(tooltipContent, { sticky: true });
                            }
                        }
                    }).addTo(map);
                    map.fitBounds(municipalityLayer.getBounds());
                    updateWardDropdown(selectedMunicipality);
                    filterTowers(selectedMunicipality);
                    if (selectedGeojsonTowers.length === 0 && towerLayer) {
                        map.removeLayer(towerLayer);
                        towerLayer = null;
                    }
                    wardDropdown.disabled = false;
                }
            });
        }

        function updateWardDropdown(municipalityFeature) {
            const wardDropdown = document.getElementById('wardDropdown');
            wardDropdown.innerHTML = '<option value="">Select a ward</option>';

            const municipalityGeometry = turf.flatten(municipalityFeature.geometry);

            allWards.features.forEach(wardFeature => {
                try {
                    const wardGeometry = turf.flatten(wardFeature.geometry);
                    const isContained = municipalityGeometry.features.some(parentPart =>
                        wardGeometry.features.some(childPart =>
                            turf.booleanContains(parentPart, childPart)
                        )
                    );

                    if (isContained) {
                        const option = document.createElement('option');
                        option.value = wardFeature.properties.name;
                        option.textContent = wardFeature.properties.name;
                        wardDropdown.appendChild(option);
                    }
                } catch (e) {
                    console.error('Ward containment error:', e);
                }
            });

            wardDropdown.addEventListener('change', function (e) {
                if (wardLayer) map.removeLayer(wardLayer);

                const selectedWardName = e.target.value;
                if (selectedWardName) {
                    const selectedWard = allWards.features.find(
                        f => f.properties.name === selectedWardName
                    );
                    wardLayer = L.geoJSON(selectedWard, {
                        style: feature => ({
                            color: '#2F4858', weight: 2, fillOpacity: 0.1
                        }),
                        onEachFeature: (feature, layer) => {
                            if (feature.properties) {
                                // Detailed tooltip with additional properties
                                const tooltipContent = `
                            <strong>${feature.properties['name:en'] || feature.properties['name']}</strong><br>
                                            
                        `;
                                layer.bindTooltip(tooltipContent, { sticky: true });
                            }
                        }
                    }).addTo(map);
                    map.fitBounds(wardLayer.getBounds());
                    filterTowers(selectedWard);
                    if (selectedGeojsonTowers.length === 0 && towerLayer) {
                        map.removeLayer(towerLayer);
                        towerLayer = null;
                    }
                }
            });
        }
    }).catch(error => {
        console.error('Error loading GeoJSON data:', error);
    });
});

const loadingModal = document.getElementById("loadingModal");

// Function to show the modal
function showLoadingModal() {
    loadingModal.classList.add("show");
}

// Function to hide the modal
function hideLoadingModal() {
    loadingModal.classList.remove("show");
}

window.sendMessage = async function () {
    const selectedTowers = [...document.querySelectorAll('#towerInfo input:checked')].map(cb => cb.value);
    const message = document.getElementById('message').value;

    if (selectedTowers.length === 0 || message.trim() === '') {
        alert('Please select at least one tower and enter a message.');
        return;
    }

    let usersToSend = new Set();

    try {
        showLoadingModal();  // Show modal before sending message
        alert("Firebase Connected! Sending message...");

        // Fetch users linked to each tower
        for (const towerId of selectedTowers) {
            const towerRef = ref(db, `user_cells/${towerId}`);
            try {
                const snapshot = await get(towerRef);
                if (snapshot.exists()) {
                    snapshot.val().forEach(user => usersToSend.add(user));
                }
            } catch (error) {
                console.error(`Error fetching users for Tower ${towerId}:`, error);
            }
        }

        usersToSend = [...usersToSend]; // Convert Set to Array
        if (usersToSend.length === 0) {
            alert("No users found for the selected towers.");
            return;
        }

        // Store the message in Firebase under each user and tower
        for (const towerId of selectedTowers) {
            for (const user of usersToSend) {
                const dbRef = ref(db, `messages/tower_${towerId}/user_${user}`);
                await set(dbRef, {
                    message: message,
                    towerId: towerId,
                    timestamp: Date.now()
                });
            }
        }

        alert(`Message sent successfully to ${usersToSend.length} users!`);
    } catch (error) {
        console.error("Error sending message:", error);
        alert("Failed to send message. Please try again.");
    } finally {
        hideLoadingModal(); // Hide modal after completion
    }
};
