function initCloudinaryBrowser(options) {
    var onConfirmCb = options && options.onConfirm;

    // ─── Modal DOM ──────────────────────────────────────────────
    var modal = document.getElementById('cloudinary-modal');
    var modalBg = document.getElementById('cloudinary-modal-bg');
    var modalClose = document.getElementById('cloudinary-modal-close');
    var modalTitle = document.getElementById('cloudinary-modal-title');
    var grid = document.getElementById('cloudinary-grid');
    var loading = document.getElementById('cloudinary-loading');
    var loadMore = document.getElementById('cloudinary-load-more');
    var btnConfirm = document.getElementById('cloudinary-btn-confirm');
    var selectedInfo = document.getElementById('cloudinary-selected-info');

    // ─── Delete confirm DOM ─────────────────────────────────────
    var delModal = document.getElementById('cloudinary-delete-confirm');
    var delBg = document.getElementById('cloudinary-delete-bg');
    var delCancel = document.getElementById('cloudinary-delete-cancel');
    var delConfirmBtn = document.getElementById('cloudinary-delete-confirm-btn');
    var delPublicId = document.getElementById('cloudinary-delete-public-id');
    var pendingDeleteId = null;

    // ─── State ──────────────────────────────────────────────────
    var currentTipo = 'imagen';
    var selectedPublicIds = new Set();
    var selectedPublicIdData = {};
    var nextCursor = null;
    var loadingImages = false;
    var totalCloudinaryCount = 0;

    // ─── API ────────────────────────────────────────────────────
    function open(tipo) {
        currentTipo = tipo || 'imagen';
        modalTitle.textContent = currentTipo === 'video'
            ? 'Explorar videos en Cloudinary'
            : 'Explorar imágenes en Cloudinary';
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        grid.innerHTML = '' +
            '<div id="cloudinary-loading" class="col-span-full flex items-center justify-center py-16">' +
                '<div class="flex flex-col items-center gap-3">' +
                    '<div class="w-8 h-8 border-4 border-primary/30 border-t-primary rounded-full animate-spin"></div>' +
                    '<p class="text-sm text-base-content/50">Cargando...</p>' +
                '</div>' +
            '</div>';
        loading = document.getElementById('cloudinary-loading');
        selectedPublicIds.clear();
        selectedPublicIdData = {};
        nextCursor = null;
        updateConfirmButton();
        fetchImages(null);
    }

    function close() {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
        selectedPublicIds.clear();
        selectedPublicIdData = {};
        updateConfirmButton();
    }

    // ─── Selection UI ───────────────────────────────────────────
    function updateConfirmButton() {
        var count = selectedPublicIds.size;
        if (count > 0) {
            selectedInfo.textContent = count + (currentTipo === 'video' ? ' video' : ' imagen')
                + (count !== 1 ? 'es' : '') + ' seleccionada' + (count !== 1 ? 's' : '');
            btnConfirm.disabled = false;
            btnConfirm.className = 'px-5 py-2 text-sm font-semibold rounded-xl transition-all bg-primary hover:bg-primary-focus text-primary-content shadow-lg shadow-primary/20 cursor-pointer';
            btnConfirm.textContent = 'Usar seleccionada' + (count > 1 ? 's (' + count + ')' : '');
        } else {
            selectedInfo.textContent = 'Ninguna ' + (currentTipo === 'video' ? 'video' : 'imagen') + ' seleccionada';
            btnConfirm.disabled = true;
            btnConfirm.className = 'px-5 py-2 text-sm font-semibold rounded-xl transition-all bg-primary/30 text-primary-content/50 cursor-not-allowed';
            btnConfirm.textContent = 'Usar seleccionada' + (currentTipo === 'video' ? 's' : '');
        }
    }

    // ─── Fetch images from API ──────────────────────────────────
    function fetchImages(cursor) {
        if (loadingImages) return;
        loadingImages = true;
        loading.classList.remove('hidden');
        loadMore.classList.add('hidden');

        var url = '/dashboard/cloudinary-imagenes/?tipo=' + currentTipo;
        if (cursor) url += '&next_cursor=' + encodeURIComponent(cursor);

        fetch(url)
            .then(function (r) { return r.json(); })
            .then(function (data) {
                loading.classList.add('hidden');
                if (data.error) {
                    grid.innerHTML = '<div class="col-span-full text-center py-16"><p class="text-error font-medium">Error: ' + data.error + '</p><p class="text-sm text-base-content/40 mt-2">Verifica la conexi&oacute;n con Cloudinary o usa el campo de URL manual.</p></div>';
                    loadingImages = false;
                    return;
                }
                if (!cursor) {
                    totalCloudinaryCount = data.total_count || 0;
                    var totalEl = document.getElementById('cloudinary-total');
                    if (totalEl) {
                        totalEl.textContent = '\u2014 ' + totalCloudinaryCount
                            + (currentTipo === 'video' ? ' videos en total' : ' im\u00e1genes en total');
                    }
                }
                if (data.images.length === 0) {
                    var emptyMsg = currentTipo === 'video'
                        ? '<div class="col-span-full text-center py-16"><p class="text-base-content/40 text-lg">📹 No se encontraron videos en Cloudinary</p><p class="text-sm text-base-content/30 mt-2">Sube videos desde el formulario o s\u00fabelos directamente a Cloudinary</p></div>'
                        : '<div class="col-span-full text-center py-16"><p class="text-base-content/40 text-lg">🖼️ No se encontraron im\u00e1genes en Cloudinary</p></div>';
                    grid.innerHTML = emptyMsg;
                    loadingImages = false;
                    return;
                }
                data.images.forEach(function (img) {
                    var div = document.createElement('div');
                    div.className = 'cloudinary-img relative aspect-square rounded-xl overflow-hidden border-2 border-transparent cursor-pointer hover:border-primary/50 transition-all group';
                    div.setAttribute('data-public-id', img.public_id);
                    div.setAttribute('data-url', img.url);
                    if (currentTipo === 'video') {
                        var thumbSrc = img.thumbnail_url || img.url;
                        div.innerHTML = '' +
                            '<img src="' + thumbSrc + '" class="w-full h-full object-cover" loading="lazy">' +
                            '<div class="absolute inset-0 flex items-center justify-center bg-black/20">' +
                                '<svg class="w-10 h-10 text-white/80" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>' +
                            '</div>' +
                            '<div class="absolute top-2 right-2 w-5 h-5 rounded-full border-2 border-white/60 transition-all selected-check"></div>' +
                            '<button type="button" class="cloudinary-delete-btn absolute bottom-1 right-1 w-6 h-6 bg-base-100/80 hover:bg-error hover:text-white text-base-content/40 rounded-full flex items-center justify-center text-xs max-lg:opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-all shadow"><svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg></button>';
                    } else {
                        div.innerHTML = '' +
                            '<img src="' + img.url + '" class="w-full h-full object-cover" loading="lazy">' +
                            '<div class="absolute inset-0 bg-primary/0 group-hover:bg-primary/10 transition-all"></div>' +
                            '<div class="absolute top-2 right-2 w-5 h-5 rounded-full border-2 border-white/60 transition-all selected-check"></div>' +
                            '<button type="button" class="cloudinary-delete-btn absolute bottom-1 right-1 w-6 h-6 bg-base-100/80 hover:bg-error hover:text-white text-base-content/40 rounded-full flex items-center justify-center text-xs max-lg:opacity-100 lg:opacity-0 lg:group-hover:opacity-100 transition-all shadow"><svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/></svg></button>';
                    }
                    div.addEventListener('click', function (e) {
                        if (e.target.closest('.cloudinary-delete-btn')) return;
                        var pid = img.public_id;
                        if (selectedPublicIds.has(pid)) {
                            selectedPublicIds.delete(pid);
                            delete selectedPublicIdData[pid];
                            div.classList.remove('border-primary', 'ring-2', 'ring-primary/50');
                            var check = div.querySelector('.selected-check');
                            if (check) {
                                check.classList.remove('bg-primary', 'border-primary');
                                check.innerHTML = '';
                            }
                        } else {
                            selectedPublicIds.add(pid);
                            selectedPublicIdData[pid] = { public_id: pid, url: img.url };
                            div.classList.add('border-primary', 'ring-2', 'ring-primary/50');
                            var check = div.querySelector('.selected-check');
                            if (check) {
                                check.classList.add('bg-primary', 'border-primary');
                                check.innerHTML = '<svg class="w-3 h-3 text-white absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"/></svg>';
                            }
                        }
                        updateConfirmButton();
                    });
                    var delBtn = div.querySelector('.cloudinary-delete-btn');
                    if (delBtn) {
                        delBtn.addEventListener('click', function (e) {
                            e.stopPropagation();
                            openDeleteConfirm(img.public_id);
                        });
                    }
                    grid.appendChild(div);
                });
                nextCursor = data.next_cursor || null;
                if (nextCursor) {
                    loadMore.classList.remove('hidden');
                } else {
                    loadMore.classList.add('hidden');
                }
                var pageInfo = document.getElementById('cloudinary-page-info');
                if (pageInfo) {
                    var shown = grid.querySelectorAll('.cloudinary-img').length;
                    if (data.has_more) {
                        pageInfo.textContent = 'Mostrando ' + shown + ' de ' + totalCloudinaryCount
                            + (currentTipo === 'video' ? ' videos' : ' im\u00e1genes');
                    } else {
                        pageInfo.textContent = 'Mostrando ' + (currentTipo === 'video' ? 'los ' : 'las ')
                            + totalCloudinaryCount + (currentTipo === 'video' ? ' videos' : ' im\u00e1genes');
                    }
                }
                loadingImages = false;
            })
            .catch(function (err) {
                loading.classList.add('hidden');
                loadingImages = false;
                grid.innerHTML = '<div class="col-span-full text-center py-16"><p class="text-error font-medium">Error de conexi\u00f3n</p><p class="text-sm text-base-content/40 mt-2">' + err.message + '</p></div>';
            });
    }

    // ─── Delete confirmation ────────────────────────────────────
    function openDeleteConfirm(publicId) {
        pendingDeleteId = publicId;
        delPublicId.textContent = publicId;
        delModal.classList.remove('hidden');
    }

    function closeDeleteConfirm() {
        delModal.classList.add('hidden');
        pendingDeleteId = null;
    }

    if (delBg) delBg.addEventListener('click', closeDeleteConfirm);
    if (delCancel) delCancel.addEventListener('click', closeDeleteConfirm);

    if (delConfirmBtn) {
        delConfirmBtn.addEventListener('click', function () {
            if (!pendingDeleteId) return;
            var pid = pendingDeleteId;
            var formData = new FormData();
            formData.append('public_id', pid);
            formData.append('tipo', currentTipo);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
            fetch('/dashboard/cloudinary-imagenes/eliminar/', {
                method: 'POST',
                body: formData,
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.error) {
                    alert('Error al eliminar: ' + data.error);
                } else {
                    var el = grid.querySelector('[data-public-id="' + pid + '"]');
                    if (el) el.remove();
                    selectedPublicIds.delete(pid);
                    delete selectedPublicIdData[pid];
                    updateConfirmButton();
                    totalCloudinaryCount = Math.max(0, totalCloudinaryCount - 1);
                    var totalEl = document.getElementById('cloudinary-total');
                    if (totalEl) {
                        totalEl.textContent = '\u2014 ' + totalCloudinaryCount
                            + (currentTipo === 'video' ? ' videos en total' : ' im\u00e1genes en total');
                    }
                }
                closeDeleteConfirm();
            })
            .catch(function () { closeDeleteConfirm(); });
        });
    }

    // ─── Event listeners ────────────────────────────────────────
    if (modalBg) modalBg.addEventListener('click', close);
    if (modalClose) modalClose.addEventListener('click', close);

    if (loadMore) {
        loadMore.addEventListener('click', function () {
            fetchImages(nextCursor);
        });
    }

    if (btnConfirm) {
        btnConfirm.addEventListener('click', function () {
            if (selectedPublicIds.size === 0) return;
            if (typeof onConfirmCb === 'function') {
                onConfirmCb({
                    tipo: currentTipo,
                    selected: Array.from(selectedPublicIds),
                    data: Object.assign({}, selectedPublicIdData),
                });
            }
            selectedPublicIds.clear();
            selectedPublicIdData = {};
            updateConfirmButton();
            close();
        });
    }

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
            close();
        }
    });

    // ─── Return public API ──────────────────────────────────────
    return {
        open: open,
        close: close,
    };
}
