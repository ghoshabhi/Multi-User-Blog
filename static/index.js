tinymce.init({
  selector: 'h2.editable',
  inline: true,
  toolbar: 'undo redo',
  menubar: false
});

tinymce.init({
  // selector: "textarea",
  mode : "exact",
  elements: "content",
  height: 500,
  plugins: [
    "advlist autolink autosave save link image lists charmap print preview hr anchor pagebreak spellchecker",
    "searchreplace wordcount visualblocks visualchars code insertdatetime media nonbreaking",
    "table contextmenu directionality emoticons template textcolor paste textcolor colorpicker textpattern"
  ],
  autosave_interval: "20s",
  toolbar1: "newdocument fullpage save | bold italic underline strikethrough | alignleft aligncenter alignright alignjustify | styleselect formatselect fontsizeselect",
  toolbar2: "cut copy paste | searchreplace | bullist numlist | outdent indent blockquote | undo redo | link unlink anchor image media code | insertdatetime preview | forecolor",
  toolbar3: "table | hr removeformat | subscript superscript | charmap emoticons | print | ltr rtl | spellchecker | visualchars visualblocks nonbreaking template pagebreak restoredraft",

  menubar: false,
  toolbar_items_size: 'small',

  style_formats: [{
    title: 'Bold text',
    inline: 'b'
  }, {
    title: 'Red text',
    inline: 'span',
    styles: {
      color: '#ff0000'
    }
  }, {
    title: 'Red header',
    block: 'h1',
    styles: {
      color: '#ff0000'
    }
  }, {
    title: 'Example 1',
    inline: 'span',
    classes: 'example1'
  }, {
    title: 'Example 2',
    inline: 'span',
    classes: 'example2'
  }, {
    title: 'Table styles'
  }, {
    title: 'Table row 1',
    selector: 'tr',
    classes: 'tablerow1'
  }],

  templates: [{
    title: 'Test template 1',
    content: 'Test 1'
  }, {
    title: 'Test template 2',
    content: 'Test 2'
  }],
  content_css: [
    '//fast.fonts.net/cssapi/e6dc9b99-64fe-4292-ad98-6974f93cd2a2.css',
    '//www.tinymce.com/css/codepen.min.css'
  ]
});

$(document).ready(function(){
  $('.postTitle h2').on('click', function() {
    $('.postTitle h2').html('');
  });
  $('.postTitle').on('focusout', function() {
    if ($('.postTitle h2').html() == '') {
      $('.postTitle h2').html('Click here to give a Title!');
    }
  });
});

$(document).on('click',':not(form)[data-confirm]',function(e){
  if(!confirm($(this).data('confirm'))){
  e.stopImmediatePropagation();
  e.preventDefault();
  }
});

$(document).on('click',':not(form)[data-confirm-post]',function(e){
  if(!confirm($(this).data('confirmPost'))){
    e.stopImmediatePropagation();
    e.preventDefault();
  }
});

$('.editComment').on('click',function(e) {
  e.preventDefault();
  postID = $(this).data('postId');
  commentID = $(this).data('commentId');
  //var url = '/comment/' + postID + '/edit/' + commentID;
  var getURL = '/comment/'+ commentID;
  $.ajax({
    type:'get',
    url: getURL,
    dataType: 'json',
    data: {},
    success: function(data){
      $('#myModal').modal('show');
      $('.modal-header h4.modal-title').text('Edit your comment here');
      $('.modal-body textarea').text(data['comment']);
      $('.modal-body textarea').focus();
    },
    error: function(data){
      alert('Sorry couldn\'t fetch the comment! Please try again!');
    }
  });

  $('.modal-footer input[type=submit]').on('click',function(e){
    var comment_str = $('#myModal textarea').val();
    $.ajax({
      type:'post',
      url: '/editcomment',
      dataType: 'json',
      data: {'postID':postID,'commentID':commentID,'comment_str':comment_str},
      success: function(){
        $('div.editComment-success').text('Comment edited successfully!');
        //$('div.editComment-success').text(data['comment_str']);
        $('div.editComment-success').css('display','block');
        $('#myModal').modal('hide');
        location.reload()
      },
      error: function(){
        //$('div.editComment-fail').text(data['comment_str']);
        $('div.editComment-fail').text('Could not edit the comment! Please try again!');
        $('div.editComment-fail').css('display','block');
        $('#myModal').modal('hide');
      }
    });
  });
});

$('.forget-password .password-change').on('click',function(){
  var email = $('#myModal input[type="email"]').val(); //works
  $.ajax({
  type: 'post',
  url: '/forgetpassword',
  dataType: 'json',
  data: {'email': email},
  success: function(data){
    if(data['result'] == "success"){
      $('.close').click();
      toastr.options = {
          "closeButton": true,
          "debug": false,
          "newestOnTop": false,
          "progressBar": true,
          "positionClass": "toast-top-full-width",
          "preventDuplicates": false,
          "onclick": null,
          "showDuration": "15000",
          "hideDuration": "1000",
          "timeOut": "15000",
          "extendedTimeOut": "1000",
          "showEasing": "swing",
          "hideEasing": "linear",
          "showMethod": "fadeIn",
          "hideMethod": "fadeOut"
        };
        toastr["info"]("<p style='font-size:20px;text-align:center'>Please check your email. You will receive a link to set your new password!</p>")
      }
      else if(data['result'] == 'invalid_email'){

      }
      else if(data['result'] == 'empty_email'){

      }
      else{
        //something went wrong!
      }
    }
  });
});

$('.btn-clippy').tooltip({
  trigger: 'click',
  placement: 'top'
});

function setTooltip(message) {
  $('.btn-clippy').tooltip('hide')
  .attr('data-original-title', message)
  .tooltip('show');
}

function hideTooltip() {
  setTimeout(function() {
    $('.btn-clippy').tooltip('hide');
  }, 10000);
}

var clipboard = new Clipboard('.btn-clippy');

clipboard.on('success', function(e) {
  setTooltip('Copied!');
  hideTooltip();
});

clipboard.on('error', function(e) {
  setTooltip('Sorry! Your browser doesn\'t support this feature');
  hideTooltip();
});

$('.like-button').on('click', function(e){
  e.preventDefault();
  var instance = $(this);
  var key = $(this).data('key');
  $.ajax({
    type: "post",
    url: "/voteup",
    dataType: 'json',
    data: {"postID": key},
    success: function(data){
      if(data['like_count'] == -1){
        toastr.options = {
          "closeButton": true,
          "debug": false,
          "newestOnTop": false,
          "progressBar": true,
          "positionClass": "toast-top-left",
          "preventDuplicates": false,
          "onclick": null,
          "showDuration": "1500",
          "hideDuration": "5000",
          "timeOut": "5000",
          "extendedTimeOut": "1000",
          "showEasing": "swing",
          "hideEasing": "linear",
          "showMethod": "fadeIn",
          "hideMethod": "fadeOut"
        };
        toastr["error"]("You cannot like your own posts!")
      }
      else if(data['like_count'] == -2){
        toastr.options = {
          "closeButton": true,
          "debug": false,
          "newestOnTop": false,
          "progressBar": true,
          "positionClass": "toast-top-left",
          "preventDuplicates": false,
          "onclick": null,
          "showDuration": "1500",
          "hideDuration": "5000",
          "timeOut": "5000",
          "extendedTimeOut": "1000",
          "showEasing": "swing",
          "hideEasing": "linear",
          "showMethod": "fadeIn",
          "hideMethod": "fadeOut"
        };
        toastr["warning"]("You have already liked this post!")
      }
      else{
        instance.parent().prev().find('span').html(data['like_count']+' likes');
        instance.addClass('disabled');
      }
    },
    error: function(data){
       toastr.options = {
          "closeButton": true,
          "debug": false,
          "newestOnTop": false,
          "progressBar": true,
          "positionClass": "toast-top-left",
          "preventDuplicates": false,
          "onclick": null,
          "showDuration": "5000",
          "hideDuration": "1000",
          "timeOut": "5000",
          "extendedTimeOut": "1000",
          "showEasing": "swing",
          "hideEasing": "linear",
          "showMethod": "fadeIn",
          "hideMethod": "fadeOut"
        };
        toastr["error"]("You have to be logged in to like a post!")
    }
  });
});

$(document).on('DOMContentLoaded', getParameterByName)

function getParameterByName() {
    const queryParams = window.location.search;
    const query = queryParams.split("?")[1];
    console.log(typeof(query));
    if (query == "updated=true") {
      //show toast
    }
}
