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
        }else if (fileType==="application/pdf" || fileType.startsWith("text/")){
            //if file is pdf and text show a message
            let pdfMessage = document.createElement("p");
            pdfMessage.textContent= "File selected: "+ file.name;
            preview.appendChild(pdfMessage);
        }
        else{
            preview.textContent= "File type is not supported for preview.";
        }
    }
});