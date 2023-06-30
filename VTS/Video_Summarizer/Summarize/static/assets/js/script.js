function submitForm() {
    var link = document.getElementById("link").value;
  
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "insert_data.php", true);
    xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    xhr.onreadystatechange = function() {
      if (this.readyState === XMLHttpRequest.DONE && this.status === 200) {
        alert(this.responseText);
      }
    };
    xhr.send("link=" + link);
}