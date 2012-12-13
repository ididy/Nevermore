#基于B/S架构的人脸识别考勤系统
***B/S — Browser/Server就是以浏览器作为系统前端与用户交互，并将数据处理工作交给服务器端***
##1. 系统结构
系统总体分为两个部分，即前端web页面和后端处理程序
###Browser端
前端web页面主要包括两方面的任务，***第一个***任务是与最终用户（员工）进行交互，使用摄像头采集照片并获得用户的输入，传输给服务器进行处理，然后接收服务器的处理结果并显示；***第二个***任务是完成系统状态查询和管理页面，主要是对数据库中存储的考勤信息进行数据可视化显示（利用各种图表显示数据），以及进行员工信息的录入和管理，还有一些考勤系统的状态显示和管理。
###Server端
服务器端也主要包括两方面的任务，***第一个***任务是获得前端传来的图像，进行人脸匹配，返回匹配结果；***第二个***任务是与数据库相关的交互，包括考勤结果录入及查询、日志、员工和管理员信息管理等，这部分需要配合前端的管理页面完成数据可视化显示和数据管理。
##2.主要实现方法
###Browser端
前端除了使用常规的html和javascript外，还要用摄像头进行图像采集，目前在浏览器中使用摄像头有3中方式：ActiveX、Flash、HTML5  
  
- ActiveX 由于只能适用于IE浏览器中，兼容性太差，所以淘汰
- Flash 的方式兼容性最好，但需要FlashPlayer插件的支持，需要学习ActionScript脚本的写法，实现起来较麻烦
- Html5 实现最简单，只需使用getUserMedia API及少量的JS代码即可，但兼容性一般，目前支持该API的浏览器有Chrome 18+（包括国内基于Chrome内核的浏览器）、Opera 12+、Firefox 16+，但Safari和IE目前尚不支持。

前端数据可视化显示，可以使用如下的JS库

- Flotr2，<http://humblesoftware.com/flotr2/>
- D3.js，<http://d3js.org>
- RGraph，<http://www.rgraph.net>

###Server端
Server端核心任务是进行人脸识别，人脸识别包括了两个步骤，  
***第一个***步骤是进行人脸检测（Face Detect），即从采集的图像中截取出人脸的部分，剔除其余的干扰，这一步骤可以使用开源的OpenCV库完成，OpenCV目前非常流行，准确度高且使用非常简单。  
***第二个***步骤是对截取出的人脸进行匹配（Face Identification），目前有很多人脸识别算法，包括Eigenface（PCA）、LDA、SVM等，参见<http://www.face-rec.org/algorithms/>，这些算法各有优缺点，有的对光线敏感，有的对方向敏感，有的对尺寸敏感，所以目前没有完美的解决方案，根据我们项目的特色，目前拟采用Eigenface算法实现，其在光照变化的条件下有96%的识别准确度，方向变化时有85%的准确度，大小变化时有64%的准确度（参见<http://en.wikipedia.org/wiki/Eigenface>）。  

Server端实现平台受制于OpenCV的支持，可供选择的语言平台有Java和Python

- 若选用Java平台，可以使用Struts2+Hibernate框架
- 若选用Python平台，可以使用web.py或其他轻量级框架

拟使用Python平台，因为本项目业务逻辑简单，如使用J2EE框架开发，则带来了不必要的复杂度，而且Python在图像处理方面有先天的优势，编码更加容易。
##目前需要解决的问题
1. 除JS外，使用Html5还是Flash作为前端的实现技术（组员中是否有人会Flash开发，ActionScript）
2. Server开发平台选择，Python是否有困难
3. 一个现实的问题，由于我们实现的系统在算法方面很难有突破，所以人脸识别率估计会有一些问题，需要考虑如果在反复尝试都无法正确识别的情况下，如何进行考勤验证
4. 任务分配：前端考勤页面开发、前端管理页面开发、前端数据可视化、后端人脸检测和识别实现、后端服务器逻辑及数据库开发
5. 组员注册GitHub帐号，<https://github.com>