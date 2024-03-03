function deleteNote(noteId) {
    fetch('/delete-note', {
        method: 'POST',
        body: JSON.stringify({ noteId: noteId }),
    }).then((_res) => {
        window.location.href = "/";
    });
}


document.getElementById("downloadPdfBtn").addEventListener("click", function() {
    var selectedNotes = document.querySelectorAll('input[name="selected_notes[]"]:checked');
    var selectedNotesIds = Array.from(selectedNotes).map(function(note) {
        return note.value;
    });

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/download-note");
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onload = function() {
        if (xhr.status === 200) {
            // Obsługa sukcesu - możesz wyświetlić powiadomienie lub podjąć inne działania
            console.log("PDF downloaded successfully");
        } else {
            // Obsługa błędu
            console.error("Failed to download PDF");
        }
    };
    xhr.send(JSON.stringify({selected_notes: selectedNotesIds}));
});
