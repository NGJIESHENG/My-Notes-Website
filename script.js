document.getElementById("fileUpload").addEventListener("change",function(event){
    let file = event.target.files[0];
    let preview = document.getElementById("preview");

    preview.innerHTML = "";

    if(file) {
        let fileType = file.type;

        if(fileType.startsWith("image/")){
            //if the file is image display it
            let img = document.createElement("img");
            img.src = URL.createObjectURL(file);
            img.style.maxWidth = "200px";
            img.style.marginTop = "10px";
            preview.appendChild(img);
        }else if (fileType==="application/pdf"){
            //if file is pdf show a message
            let pdfMessage = document.createElement("p");
            pdfMessage.textContent= "PDF selected: "+ file.name;
            preview.appendChild(pdfMessage);
        }else if (fileType.startsWith("text/")){
            //if its a text file display its content
            let reader = new FileReader();
            reader.onload = function(e){
                let textPreview = document.createElement("pre");
                textPreview.textContent = e.target.result;
                preview.appendChild(textPreview);
            };
            reader.readAsText(file);
        }else{
            preview.textContent= "File type is not supported for preview.";
        }
    }
});