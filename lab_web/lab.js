/* Laboratuvar değerlendirmeleri finansal kayıttan bağımsız tutulur. */
'use strict';
let labFeedback = {};
let labSyncTimer;
let labReady = false;
let labModels = [];
let labDocumentReaders = {};
let labCurrentDocument = null;
let labMetadataLoading = false;
let labSelectedReader = localStorage.getItem('lab-reader') || 'paddle';

// Yalnızca laboratuvar yüklemelerine motor tercihi eklenir.
const labNativeFetch = window.fetch.bind(window);
window.fetch = (input, options) => {
  if (typeof input === 'string' && input.startsWith('/api/uploads')) {
    const url = new URL(input, location.origin);
    url.searchParams.set('reader', labSelectedReader);
    input = url.pathname + url.search;
  }
  return labNativeFetch(input, options);
};

async function loadLabFeedback() {
  const response = await fetch('/api/lab');
  if (!response.ok) throw new Error('Test bilgileri alınamadı.');
  const data = await response.json();
  labModels = data.models;
  labDocumentReaders = data.readers_by_document || {};
  if (!labModels.some((model) => model.id === labSelectedReader && model.available))
    labSelectedReader = 'prototype';
  const selector = document.querySelector('#lab-reader');
  selector.replaceChildren(
    ...labModels.map((model) => {
      const option = document.createElement('option');
      option.value = model.id;
      option.textContent = model.name + (model.available ? '' : ' · hazır değil');
      option.disabled = !model.available;
      return option;
    }),
  );
  selector.value = labSelectedReader;
  document.querySelector('#lab-reader-note').textContent =
    'Yeni yüklemeler bu motorla okunur. Belgeler cihazınızda kalır.';
  labReady = true;
  labFeedback = Object.fromEntries(data.feedback.map((entry) => [entry.document_id, entry]));
}

function syncLabPage() {
  if (!labReady) return;
  const heading = document.querySelector('#app h1');
  if (heading?.textContent === 'Her fatura, kontrol altında.') {
    heading.textContent = 'Belge okumasını birlikte ölçelim.';
  }
  document.querySelectorAll('[data-action="approve"] span').forEach((label) => {
    if (label.textContent !== 'Referans olarak doğrula')
      label.textContent = 'Referans olarak doğrula';
  });
  const id = location.hash.match(/^#document\/([a-f0-9]{32})$/)?.[1];
  if (id && id !== labCurrentDocument && !labMetadataLoading) {
    labCurrentDocument = id;
    labMetadataLoading = true;
    loadLabFeedback().finally(() => {
      labMetadataLoading = false;
      syncLabPage();
    });
    return;
  }
  if (labMetadataLoading) return;
  const form = document.querySelector('.review-form');
  const ready = document.querySelector('[data-path="invoice_number"]');
  const progress = document.querySelector('.processing-panel');
  if (progress && !document.querySelector('#lab-progress-note')) {
    const note = document.createElement('p');
    note.id = 'lab-progress-note';
    note.textContent =
      'Yerel model yüklemesi ve üretim birkaç dakika sürebilir. Denemeler bellek kullanımı için sırayla çalıştırılır.';
    progress.append(note);
  }
  if (!id || !form || !ready || document.querySelector('#lab-feedback')) return;
  const panel = document.createElement('section');
  panel.className = 'card form-card lab-feedback';
  panel.id = 'lab-feedback';
  panel.innerHTML = `
    <h2>Bu okuma nasıl sonuçlandı?</h2>
    <p><b id="lab-result-reader"></b></p>
    <div class="lab-compare-row">
      <select id="lab-comparison-reader" aria-label="Karşılaştırılacak motor"></select>
      <button class="btn btn-light" id="lab-run-reader">Bu belgeyi seçili motorla dene</button>
    </div>
    <p id="lab-run-message" role="status"></p>
    <p>Okunan alanları belgeyle karşılaştırın. Alan düzeltmelerini aşağıdaki
    <b>Taslak kaydet</b> veya <b>Referans olarak doğrula</b> düğmesiyle saklayın.
    Buradaki notlar yalnızca model testinde kullanılır.</p>
    <label class="field"><span>Okuma sonucu</span>
      <select id="lab-rating">
        <option value="">Seçin</option>
        <option value="pass">Başarılı · alanlar doğru</option>
        <option value="partial">Kısmen doğru · düzeltme gerekiyor</option>
        <option value="fail">Hatalı · yeniden çalışılmalı</option>
      </select>
    </label>
    <label class="field" style="margin-top:14px"><span>Hatalı veya eksik alanlar</span>
      <textarea id="lab-notes" rows="3" placeholder="Örnek: Fatura numarasındaki A, 4 okunmuş. İkinci ürün eksik."></textarea>
    </label>
    <button id="lab-save-feedback" class="btn btn-primary">Test sonucunu kaydet</button>
    <div class="lab-score" id="lab-message" role="status"></div>`;
  form.prepend(panel);
  const activeReader = labDocumentReaders[id] || 'prototype';
  panel.querySelector('#lab-result-reader').textContent =
    'Bu sonucun motoru: ' +
    (labModels.find((model) => model.id === activeReader)?.name || activeReader);
  const comparison = panel.querySelector('#lab-comparison-reader');
  comparison.replaceChildren(
    ...labModels.map((model) => {
      const option = document.createElement('option');
      option.value = model.id;
      option.textContent = model.name;
      option.disabled = !model.available;
      return option;
    }),
  );
  comparison.value =
    labModels.find((model) => model.id !== activeReader && model.available)?.id || activeReader;
  panel.querySelector('#lab-run-reader').onclick = async (event) => {
    event.target.disabled = true;
    try {
      const response = await fetch(`/api/lab/${id}/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reader: comparison.value }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error);
      location.hash = `document/${result.id}`;
    } catch (error) {
      panel.querySelector('#lab-run-message').textContent = error.message;
    } finally {
      event.target.disabled = false;
    }
  };
  const saved = labFeedback[id];
  panel.querySelector('#lab-rating').value = saved?.rating || '';
  panel.querySelector('#lab-notes').value = saved?.notes || '';
  if (saved) panel.querySelector('#lab-message').textContent = 'Önceki değerlendirmeniz yüklendi.';
  panel.querySelector('#lab-save-feedback').addEventListener('click', async (event) => {
    const button = event.target;
    button.disabled = true;
    const message = panel.querySelector('#lab-message');
    try {
      const response = await fetch(`/api/lab/${id}/feedback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          rating: panel.querySelector('#lab-rating').value,
          notes: panel.querySelector('#lab-notes').value,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error);
      await loadLabFeedback();
      message.textContent = 'Test değerlendirmeniz kaydedildi. ERP kayıtları değişmedi.';
    } catch (error) {
      message.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}

new MutationObserver(() => {
  clearTimeout(labSyncTimer);
  labSyncTimer = setTimeout(syncLabPage, 40);
}).observe(document.querySelector('#app'), { childList: true, subtree: true });

loadLabFeedback()
  .then(syncLabPage)
  .catch((error) => console.warn(error.message));

document.querySelector('#lab-reader').addEventListener('change', (event) => {
  labSelectedReader = event.target.value;
  localStorage.setItem('lab-reader', labSelectedReader);
});
