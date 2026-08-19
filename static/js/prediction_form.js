/**
 * static/js/prediction_form.js
 * JavaScript logic for Smart Matching Recommendations on Prediction Request Page
 */

document.addEventListener("DOMContentLoaded", function () {
  const btnRunMatching = document.getElementById("btnRunMatching");
  const matchingDataEl = document.getElementById("matching-data");
  const selectChild = document.getElementById("id_child");
  const selectFamily = document.getElementById("id_family");

  const matchingPromptState = document.getElementById("matchingPromptState");
  const matchingLoadingState = document.getElementById("matchingLoadingState");
  const matchingListContent = document.getElementById("matchingListContent");

  if (!btnRunMatching || !matchingDataEl) return;

  const matchingUrl = matchingDataEl.getAttribute("data-url");

  btnRunMatching.addEventListener("click", function () {
    const childId = selectChild ? selectChild.value : "";
    const familyId = selectFamily ? selectFamily.value : "";

    if (!childId && !familyId) {
      alert("Please select a Child Record or a Candidate Foster Family first.");
      return;
    }

    // Show loading state
    if (matchingPromptState) matchingPromptState.classList.add("d-none");
    if (matchingLoadingState) matchingLoadingState.classList.remove("d-none");
    if (matchingListContent) matchingListContent.innerHTML = "";

    let reqUrl = matchingUrl + "?";
    if (childId) {
      reqUrl += "child_id=" + encodeURIComponent(childId);
    } else if (familyId) {
      reqUrl += "family_id=" + encodeURIComponent(familyId);
    }

    fetch(reqUrl)
      .then((res) => {
        if (!res.ok) throw new Error("Server error fetching recommendations");
        return res.json();
      })
      .then((data) => {
        if (matchingLoadingState) matchingLoadingState.classList.add("d-none");

        const matches = data.matches || [];
        if (matches.length === 0) {
          matchingListContent.innerHTML = `
            <div class="text-center my-auto py-4 text-muted">
              <i class="bi bi-info-circle fs-3 text-warning mb-2" aria-hidden="true"></i>
              <h4 class="h6 font-weight-bold">No High-Suitability Matches Found</h4>
              <p class="small text-muted mb-0">No candidates met the minimum compatibility threshold or hard constraint pre-filters.</p>
            </div>`;
          return;
        }

        let html = `<div class="list-group list-group-flush border-top border-bottom overflow-auto flex-grow-1 mb-2" style="max-height:360px;">`;
        matches.forEach((item) => {
          const badgeClass = item.badge_class || "primary";
          const badgeLabel = item.badge_label || "Match";
          const scorePct = item.score_percent !== undefined ? item.score_percent : Math.round((item.compatibility_score || 0) * 100);

          if (data.mode === "child") {
            html += `
              <div class="list-group-item list-group-item-action py-3">
                <div class="d-flex w-100 justify-content-between align-items-center mb-1">
                  <h6 class="mb-0 font-weight-bold text-dark">${escapeHtml(item.name)}</h6>
                  <span class="badge bg-${badgeClass}">${scorePct}% ${badgeLabel}</span>
                </div>
                <p class="small text-muted mb-1">
                  <i class="bi bi-geo-alt me-1"></i>${escapeHtml(item.state || "")} &bull; Capacity: ${item.capacity} (${item.available_slots} available slots) &bull; Experience: ${item.experience_years} yrs
                </p>
                ${item.explanation_summary ? `<div class="small text-secondary fst-italic">${escapeHtml(item.explanation_summary)}</div>` : ""}
              </div>`;
          } else {
            html += `
              <div class="list-group-item list-group-item-action py-3">
                <div class="d-flex w-100 justify-content-between align-items-center mb-1">
                  <h6 class="mb-0 font-weight-bold text-dark">${escapeHtml(item.name)}</h6>
                  <span class="badge bg-${badgeClass}">${scorePct}% ${badgeLabel}</span>
                </div>
                <p class="small text-muted mb-1">
                  <i class="bi bi-person me-1"></i>Age ${item.age} (${item.gender}) &bull; ${escapeHtml(item.state || "")} &bull; Time in care: ${item.time_in_care_months} mos
                </p>
                ${item.explanation_summary ? `<div class="small text-secondary fst-italic">${escapeHtml(item.explanation_summary)}</div>` : ""}
              </div>`;
          }
        });
        html += `</div>`;
        matchingListContent.innerHTML = html;
      })
      .catch((err) => {
        if (matchingLoadingState) matchingLoadingState.classList.add("d-none");
        if (matchingListContent) {
          matchingListContent.innerHTML = `
            <div class="text-center my-auto py-4 text-danger">
              <i class="bi bi-exclamation-triangle fs-3 mb-2" aria-hidden="true"></i>
              <h4 class="h6 font-weight-bold">Error Loading Recommendations</h4>
              <p class="small mb-0">${escapeHtml(err.message)}</p>
            </div>`;
        }
      });
  });

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
});
