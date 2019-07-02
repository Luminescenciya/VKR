$(document).ready(function(){
	myCodeMirror.setSize(500, 300);
	var myTextArea = document.getElementById('editTask');
	var editor = CodeMirror.fromTextArea(myTextArea);
})
