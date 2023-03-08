db_config = {
    'user': 'admin', 
    'password': 'admin1234',
    'host': 'database-2.cndu2rjoy9bs.us-east-1.rds.amazonaws.com',
    'database': 'elogin'
}

app_config = {
    'MAIL_SERVER' : 'smtp.gmail.com',
    'MAIL_PORT' : 465,
    'MAIL_USE_SSL' : True,
    'MAIL_USERNAME' : "ece1779assignment@gmail.com",
    'MAIL_PASSWORD' : "Test@123",
    'MAIL_USE_TLS' : False,
    'MAX_CONTENT_LENGTH' : 10 * 1024 * 1024,
    'UPLOAD_EXTENSIONS' : ['.jpg', '.png', '.jpeg'],
    'MEDIA_PATH' : 'media',
    'UPLOAD_PATH' : 'static/media',
    'THUMBNAIL_SIZE' : (200, 200),
    'THUMBNAIL_FOLDER' : 'thumbnail',
    'THUMBNAIL_FORMAT' : 'png',
    'BLUR_FOLDER' : 'blur',
    'SHADE_FOLDER' : 'shade',
    'SPREAD_FOLDER' : 'spread',
    'API_KEY' : 'AIzaSyAtJOCdO24H8i3EyJMrQsVltgppoXgiooI',
    'API_URL' : 'https://maps.googleapis.com/maps/api/distancematrix/json?',
    'RADIUS' : 5
} 

s3_config = {
    'REGION_NAME' : 'us-east-1',
    'ENDPOINT_URL' : 'http://a2ece1779.s3.amazonaws.com/',
    'AWS_ACCESS_KEY' : 'AKIA5LVZUYZYUNXOVFUJ',
    'AWS_SECRET_KEY' : "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",
    'BUCKET_NAME' : "a2ece1779"
}