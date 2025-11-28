function detectCycle(constraints) {
    const graph = {};
    const indegree = {};
    const nodes = new Set();
    constraints.forEach(([from, to]) => {
        if (!graph[from]) graph[from] = [];
        graph[from].push(to);
        nodes.add(from);
        nodes.add(to);
        indegree[to] = (indegree[to] || 0) + 1;
        if (!(from in indegree)) indegree[from] = 0;
    });
    const queue = [];
    nodes.forEach(node => {
        if (indegree[node] === 0) queue.push(node);
    });
    let visited = 0;
    while (queue.length > 0) {
        const node = queue.shift();
        visited++;
        if (graph[node]) {
            graph[node].forEach(nei => {
                indegree[nei]--;
                if (indegree[nei] === 0) {
                    queue.push(nei);
                }
            });
        }
    }
    return visited < nodes.size;
}

function toggleInputsDisabled(section, disable) {
    const inputs = section.querySelectorAll('input, select');
    inputs.forEach(input => {
        input.disabled = disable;
    });
}

function checkLocationLimit() {
    const limit = 8;
    const allCheckboxes = document.querySelectorAll('input[name="locations"]');
    const checkedCount = document.querySelectorAll('input[name="locations"]:checked').length;

    const limitReached = (checkedCount >= limit);

    allCheckboxes.forEach(cb => {
        if (!cb.checked) {
            cb.disabled = limitReached;
            const summary = cb.closest('.location-summary');
            if (summary) {
                if (limitReached) {
                    summary.style.opacity = '0.6';
                    summary.style.cursor = 'not-allowed';
                } else {
                    summary.style.opacity = '1';
                    summary.style.cursor = 'pointer';
                }
            }
        }
    });
}

const selectedListEmptyItem = `
    <li class="selected-placeholder">
        <i class="fa-regular fa-compass"></i>
        <span>No locations selected yet</span>
    </li>`;

function updateRightColumnSelections() {
    const checkboxes = document.querySelectorAll('input[name="locations"]:checked');
    const startSelect = document.getElementById('start_point_select');
    const endSelect = document.getElementById('end_point_select');
    const selectedList = document.getElementById('selected-locations-list');

    const oldStartVal = startSelect.value;
    const oldEndVal = endSelect.value;

    startSelect.innerHTML = '<option value="">-- Select start point --</option>';
    endSelect.innerHTML = '<option value="">-- Select end point --</option>';
    selectedList.innerHTML = '';

    if (checkboxes.length === 0) {
        selectedList.innerHTML = selectedListEmptyItem;
    } else {
        checkboxes.forEach((cb, idx) => {
            const id = cb.value;
            const name = cb.dataset.locationName;

            startSelect.innerHTML += `<option value="${id}">${name}</option>`;
            endSelect.innerHTML += `<option value="${id}">${name}</option>`;
            selectedList.innerHTML += `
                <li class="selected-location-item">
                    <span class="location-order">${idx + 1}</span>
                    <span class="location-name">${name}</span>
                </li>`;
        });
    }

    startSelect.value = oldStartVal;
    endSelect.value = oldEndVal;

    checkLocationLimit();
}

function updatePrecedenceDropdowns() {
    const selectedCheckboxes = document.querySelectorAll('input[name="locations"]:checked');
    const selectedIds = Array.from(selectedCheckboxes).map(cb => cb.value);

    document.querySelectorAll('.precedence-dropdown').forEach(dropdown => {
        const currentId = dropdown.getAttribute('data-current-id');

        Array.from(dropdown.options).forEach(option => {
            const optVal = option.value;
            const shouldHide = optVal === "" || optVal === currentId || !selectedIds.includes(optVal);
            option.hidden = shouldHide;
            if (shouldHide && dropdown.value === optVal) {
                dropdown.value = "";
            }
        });
    });
}

function updatePinnedInputsVisibility() {
    const selectedStart = document.getElementById('start_point_select').value;
    const selectedEnd = document.getElementById('end_point_select').value;

    const hiddenIds = new Set();
    if (selectedStart) hiddenIds.add(selectedStart);
    if (selectedEnd) hiddenIds.add(selectedEnd);

    document.querySelectorAll('.extra-inputs').forEach(div => {
        const locationId = div.closest('.details-section').id.replace('details-section-', '');
        if (hiddenIds.has(locationId)) {
            div.style.display = 'none';
        } else {
            div.style.display = 'block';
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const checkboxes = document.querySelectorAll('input[name="locations"]');

    checkboxes.forEach(checkbox => {
        const targetId = checkbox.dataset.target;
        const detailsSection = document.querySelector(targetId);
        const summary = checkbox.closest('.location-summary');

        if (!checkbox.checked) {
            detailsSection.style.display = 'none';
            toggleInputsDisabled(detailsSection, true);
        } else {
            detailsSection.style.display = 'block';
            toggleInputsDisabled(detailsSection, false);
        }

        checkbox.addEventListener('change', function () {
            if (this.checked) {
                detailsSection.style.display = 'block';
                toggleInputsDisabled(detailsSection, false);
            } else {
                detailsSection.style.display = 'none';
                toggleInputsDisabled(detailsSection, true);
            }
            updateRightColumnSelections();
        });

        const label = checkbox.closest('.location-summary');
        if (label) {
            label.addEventListener('click', function (e) {
                if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON' || e.target.closest('button')) {
                    e.stopPropagation();
                    return;
                }

                if (e.target.tagName !== 'INPUT') {
                    const checkedCount = document.querySelectorAll('input[name="locations"]:checked').length;
                    if (!checkbox.checked && checkedCount >= 8) {
                        alert("You can only select a maximum of 8 locations.");
                        e.preventDefault();
                        return;
                    }

                    checkbox.checked = !checkbox.checked;
                    checkbox.dispatchEvent(new Event('change'));
                }
            });
        }
    });

    document.getElementById('start_point_select').addEventListener('change', updatePinnedInputsVisibility);
    document.getElementById('end_point_select').addEventListener('change', updatePinnedInputsVisibility);

    const createJourneyButton = document.getElementById('create-journey-button');
    if (createJourneyButton) {
        createJourneyButton.addEventListener('click', function (e) {
            const constraints = [];
            const dropdowns = document.querySelectorAll('.precedence-dropdown');

            dropdowns.forEach(dropdown => {
                const afterId = dropdown.value;
                const currentId = dropdown.getAttribute('data-current-id');

                if (afterId && !dropdown.disabled) {
                    constraints.push([afterId, currentId]);
                }
            });

            if (detectCycle(constraints)) {
                e.preventDefault();
                alert("Error: A cycle was detected in the precedence constraints.\nPlease check your 'Must go after' selections.");
            }
        });
    }

    updateRightColumnSelections();
    updatePrecedenceDropdowns();
    updatePinnedInputsVisibility();

    const tripGuideModal = document.getElementById('trip-guide-modal');
    const openGuideBtn = document.getElementById('open-trip-guide');
    const closeGuideBtn = document.getElementById('close-trip-guide');
    const guideStartBtn = document.getElementById('guide-start-select');

    function toggleTripGuide(show) {
        if (!tripGuideModal) return;
        tripGuideModal.classList.toggle('is-visible', show);
        document.body.classList.toggle('modal-open', show);
        tripGuideModal.setAttribute('aria-hidden', show ? 'false' : 'true');
    }

    openGuideBtn?.addEventListener('click', () => toggleTripGuide(true));
    closeGuideBtn?.addEventListener('click', () => toggleTripGuide(false));
    tripGuideModal?.addEventListener('click', (e) => {
        if (e.target === tripGuideModal) toggleTripGuide(false);
    });
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') toggleTripGuide(false);
    });
    guideStartBtn?.addEventListener('click', () => {
        toggleTripGuide(false);
        document.querySelector('.location-list-column')?.scrollIntoView({ behavior: 'smooth' });
    });
});
