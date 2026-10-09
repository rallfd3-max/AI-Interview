-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: aiinterviewerdb
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admin`
--

DROP TABLE IF EXISTS `admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admin` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户名',
  `password` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '密码',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `username` (`username`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='运营管理平台的admin级别用户';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin`
--

LOCK TABLES `admin` WRITE;
/*!40000 ALTER TABLE `admin` DISABLE KEYS */;
INSERT INTO `admin` VALUES (1,'admin','123123'),(2,'wst','123456'),(3,'xiaoming','123456');
/*!40000 ALTER TABLE `admin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `answer_record`
--

DROP TABLE IF EXISTS `answer_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `answer_record` (
  `id` varchar(24) NOT NULL,
  `candidate_id` varchar(255) DEFAULT NULL,
  `job_name` varchar(255) DEFAULT NULL,
  `answer` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `answer_record`
--

LOCK TABLES `answer_record` WRITE;
/*!40000 ALTER TABLE `answer_record` DISABLE KEYS */;
INSERT INTO `answer_record` VALUES ('1913074634872602626','1878381840839602177','java工程师','乐观所是，一种基于冲突，是偶然的这一假设的锁机制。'),('1913074634901962754','1878381840839602177','java工程师',' Hash map中添加减值对时，首先会对通过键的SQL的方法获取其还是。'),('1913074634964877313','1878381840839602177','java工程师',' Collection是Java几何框架中的一个接口，它处于几何框架中的顶层，定义了集合的结构规范。'),('1913075740130426881','1878381840839602177','web前端工程师',''),('1913075740130426882','1878381840839602177','web前端工程师',''),('1913075740197535746','1878381840839602177','web前端工程师',''),('1913077109050589186','1878381840839602177','web前端工程师',''),('1913077109113503745','1878381840839602177','web前端工程师',''),('1913077109113503746','1878381840839602177','web前端工程师',''),('1913078717331292161','1878381840839602177','web前端工程师',''),('1913078717331292162','1878381840839602177','web前端工程师',''),('1913078717394206722','1878381840839602177','web前端工程师',''),('1913079449098985474','1878381840839602177','web前端工程师',''),('1913079449098985475','1878381840839602177','web前端工程师',''),('1913079449170288642','1878381840839602177','web前端工程师',''),('1913080859257544705','1878381840839602177','web前端工程师','乐观所是，一种基于冲突，是偶然的最佳生活机制，他认为在多线程环境下，数据冲突发生的概率较低。'),('1913080859324653570','1878381840839602177','web前端工程师','悲观所是一种基于众多事普遍的这一假设的诉求机制，他认为在多线程环境下数据发生冲突是很常见的现象。'),('1913080859387568129','1878381840839602177','web前端工程师',NULL),('1941455368611987457','1878381840839602177','123',''),('1941455368695873537','1878381840839602177','123',''),('1941455368762982402','1878381840839602177','123',''),('1941468152376623105','1878381840839602177','web前端工程师','悲观所是一种基于冲突是普遍的这一假设的所机制。'),('1941468152376623106','1878381840839602177','web前端工程师',' Collection是Java集合框架中的一个接口。'),('1941468152439537666','1878381840839602177','web前端工程师','哈希map使用哈希表来存储键值对。'),('1945768264116547586','1945763916984692738','java工程师','哈希map使用哈希表存储键值对。'),('1945768264242376705','1945763916984692738','java工程师',' Selection是Java集合框架中的一种接口。'),('1945768264309485570','1945763916984692738','java工程师','乐观所是一种基于冲突是偶然的这一假设的手机制。'),('1949173414722043906','1945763916984692738','java工程师',''),('1949173414789152769','1945763916984692738','java工程师',''),('1949173414852067329','1945763916984692738','java工程师',''),('1949346148361981953','1945763916984692738','java工程师','追追追。'),('1949346148408119297','1945763916984692738','java工程师','是不是？'),('1949346148471033857','1945763916984692738','java工程师','十字。'),('1949459725114671105','1945763916984692738','java工程师',' Collections是Java集合框架中的一个接口。'),('1949459725135642626','1945763916984692738','java工程师','不知道。'),('1949459725198557185','1945763916984692738','java工程师','不知道。'),('1952295325299638273','1945763916984692738','java工程师',NULL),('1952295325509353474','1945763916984692738','java工程师','你好，哼。?'),('1952295325572268033','1945763916984692738','java工程师',NULL),('1952297382102446081','1945763916984692738','java工程师','乐观所是遇是一种机遇，冲突是偶然的这一假设的所机制。'),('1952297382102446082','1945763916984692738','java工程师','Hsh map使用hah表来存储定制对。'),('1952297382169554945','1945763916984692738','java工程师','colelection是加华集合框架中的一个接口。'),('1954465918488965121','1945763916984692738','java工程师',''),('1954465918593822722','1945763916984692738','java工程师','好的。?'),('1954465918669320193','1945763916984692738','java工程师','不知道。?'),('1957446412876926978','1945763916984692738','java工程师',''),('1957446412969201666','1945763916984692738','java工程师',''),('1957446413027921921','1945763916984692738','java工程师',''),('1957758670358257666','1945763916984692738','java工程师','继承了王族的血脉，瓦森通过内线得知了阿朱兰的大致情况。。'),('1957758670416977921','1945763916984692738','java工程师','哈hy map使用哈y表来存储建支队。'),('1957758670475698177','1945763916984692738','java工程师','乐观锁是一种基于冲突是偶然的这一假设的所机制。'),('1957844636007710722','1945763916984692738','java工程师','你好。?'),('1957844636028682242','1945763916984692738','java工程师','と？'),('1957844636095791106','1945763916984692738','java工程师','2.'),('1957989720388829185','1945763916984692738','java工程师','collection是加法集合框架中的一个接口。'),('1957989720510464002','1945763916984692738','java工程师','悲观锁是是一种基于冲突式普遍的这一假设的所机制。'),('1957989720573378561','1945763916984692738','java工程师','哈sh map使用哈西表来存储建支队。'),('1957990256232136706','1945763916984692738','java工程师','collection是加法集合框架中的一个接口。'),('1957990256295051265','1945763916984692738','java工程师','悲观锁是是一种基于冲突式普遍的这一假设的所机制。'),('1957990256362160130','1945763916984692738','java工程师','哈sh map使用哈西表来存储建支队。'),('1957990518611017729','1945763916984692738','java工程师','collection是加法集合框架中的一个接口。'),('1957990518648766466','1945763916984692738','java工程师','悲观锁是是一种基于冲突式普遍的这一假设的所机制。'),('1957990518690709506','1945763916984692738','java工程师','哈sh map使用哈西表来存储建支队。'),('1958003832233689089','1957999403661033473','java工程师',''),('1958003832317575169','1957999403661033473','java工程师',''),('1958003832380489730','1957999403661033473','java工程师',''),('1958004129978941441','1957999403661033473','java工程师',''),('1958004130037661697','1957999403661033473','java工程师',''),('1958004130104770562','1957999403661033473','java工程师',''),('1958115696825462785','1957999403661033473','java工程师',''),('1958115696963874818','1957999403661033473','java工程师','乐观所是一种基于冲突是偶然的这一假设的锁机制。'),('1958115697043566594','1957999403661033473','java工程师','悲观所系是一种基于冲突式普遍的这一假设的所机制。'),('1961337984479731714','1957999403661033473','java工程师','乐观锁是一种基于冲突是普遍的这一假设索机制。'),('1961338007116390402','1957999403661033473','java工程师','哈西迈不逊哈希表达村市竞支队。'),('1961338007191887873','1957999403661033473','java工程师','被一关锁是一种基于冲度是普遍的这一假设的所机制。'),('1961356214850121730','1957999403661033473','java工程师',''),('1961356214850121731','1957999403661033473','java工程师',''),('1961356214980145154','1957999403661033473','java工程师',''),('1961356611392204801','1957999403661033473','java工程师',''),('1961356611455119362','1957999403661033473','java工程师',''),('1961356611522228225','1957999403661033473','java工程师',''),('1961401438162952193','1957999403661033473','java工程师',NULL),('1961401438230061057','1957999403661033473','java工程师',NULL),('1961401438230061058','1957999403661033473','java工程师',NULL),('1961696389585215490','1957999403661033473','java工程师','乐观锁是一种基于冲突式偶然的这一假设的所机制。'),('1961696389660712962','1957999403661033473','java工程师','sh map使用哈西表来存储建制队。'),('1961696389660712963','1957999403661033473','java工程师','悲观所是一种基于冲突式普遍的这一架设的服机制。'),('1961984129459585025','1957999403661033473','java工程师','?他们得到金奖的一个经验，他们也是这个想。'),('1961984129530888193','1957999403661033473','java工程师','都来得及晚。'),('1961984129530888194','1957999403661033473','java工程师','那你们反正上午上课能够实时去。'),('1961992850726223874','1957999403661033473','java工程师','让候选人感觉非常。'),('1961992850793332737','1957999403661033473','java工程师','江话无法应活应对不同货选若。面试结束后，往往没有闭环，缺乏有效。'),('1961992850856247297','1957999403661033473','java工程师','情是么他看分析他看一。'),('1961996503407165441','1957999403661033473','java工程师','collection是加码集合框架中的一个接口。'),('1961996503474274305','1957999403661033473','java工程师','h map使用哈希表来存储建制队。'),('1961996503537188865','1957999403661033473','java工程师','一答题我不知道。'),('1962042149002575873','1957999403661033473','java工程师','不知道。?'),('1962042149002575874','1957999403661033473','java工程师','不知道。?'),('1962042149065490433','1957999403661033473','java工程师','不会。?'),('1962406969845510146','1957999403661033473','java工程师',NULL),('1962406969883258881','1957999403661033473','java工程师',NULL),('1962406969962950658','1957999403661033473','java工程师',NULL),('1962492684889518082','1957999403661033473','java工程师',NULL),('1962492684944044033','1957999403661033473','java工程师',NULL),('1962492684994375682','1957999403661033473','java工程师','三年级就是建立在我可以的情况下，我们现在这会。'),('1962774346043011074','1957999403661033473','java工程师',''),('1962774346076565505','1957999403661033473','java工程师','?靠，你点也没问记。'),('1962774346139480065','1957999403661033473','java工程师','几项。'),('1962789543533146113','1957999403661033473','java工程师','你好。'),('1962789543621226497','1957999403661033473','java工程师',''),('1962789543621226498','1957999403661033473','java工程师','严爽。'),('1967211234610925570','1957999403661033473','java工程师',NULL),('1967211234703200257','1957999403661033473','java工程师',NULL),('1967211234778697729','1957999403661033473','java工程师',NULL),('2007105230392819713','1963195861045669889','java工程师',NULL),('2007105230489288706','1963195861045669889','java工程师',NULL),('2007105230560591874','1963195861045669889','java工程师',NULL),('2008425960460095489','1957999403661033473','java工程师',NULL),('2008425960552370178','1957999403661033473','java工程师',NULL),('2008425960611090434','1957999403661033473','java工程师',NULL),('2008486961834409985','1957999403661033473','java工程师',NULL),('2008486961943461890','1957999403661033473','java工程师',NULL),('2008486962023153666','1957999403661033473','java工程师',NULL);
/*!40000 ALTER TABLE `answer_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `candidate`
--

DROP TABLE IF EXISTS `candidate`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `candidate` (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `real_name` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '真实姓名（需国密）',
  `identity_num` varchar(18) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '应聘者身份证号码',
  `mobile` varchar(11) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '应聘者手机号',
  `sex` int DEFAULT NULL COMMENT '性别，1:男 0:女 2:保密',
  `face` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '应聘者照片',
  `email` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '邮箱',
  `birthday` date DEFAULT NULL COMMENT '生日',
  `country` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '国家',
  `province` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '省份',
  `city` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '城市',
  `district` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '区县',
  `address` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '地址',
  `job_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '应聘职位的主键id',
  `remark` varchar(1280) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '备注信息',
  `created_time` datetime NOT NULL COMMENT '创建时间',
  `updated_time` datetime NOT NULL COMMENT '更新时间',
  `job` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `job_can` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `school` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '学校',
  `major` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '专业',
  `certificate` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '证书',
  `awards` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '奖项',
  `experiment` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `introduce` varchar(4000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '个人介绍',
  `job_name` int DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE KEY `mobile` (`mobile`) USING BTREE,
  UNIQUE KEY `identity_num` (`identity_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='应聘者表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `candidate`
--

LOCK TABLES `candidate` WRITE;
/*!40000 ALTER TABLE `candidate` DISABLE KEYS */;
INSERT INTO `candidate` VALUES ('1942861998512607233','刘龙翔','1234567890123456','13318498005',1,NULL,'878997222@qq.com',NULL,NULL,NULL,NULL,NULL,NULL,'1878381728411283458',NULL,'2025-07-09 16:22:52','2025-07-09 16:22:52',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),('1957744925842096129','小陈','360124201008024252','13671780788',0,NULL,'1871847984@qq.com','2025-08-14',NULL,NULL,NULL,NULL,NULL,'1945763660796604418',NULL,'2025-08-19 18:02:18','2025-08-19 18:02:18',NULL,NULL,'无','无','无','无','无','无',NULL),('1957999403661033473','吴**','123123123123123123','13671790755',1,NULL,'1871847981@qq.com',NULL,NULL,NULL,NULL,NULL,NULL,'1945763660796604418',NULL,'2025-08-20 10:53:30','2026-01-06 18:32:24',NULL,NULL,'','','','','','',NULL),('1961719081678761985','李四','897287788090987987','12345678901',1,NULL,'123456@qq.com','2004-08-12',NULL,NULL,NULL,NULL,NULL,'1961717937057394690',NULL,'2025-08-30 17:14:11','2026-01-06 14:32:04','算法工程师',NULL,'清华大学','计算机科学','英语四六级','ACM团队赛国家级一等奖','曾经写过一个ai面试官的项目。\\n','我是李四，毕业于清华大学计算机科学专业，拥有三年以上 Python 后端开发经验，擅长使用 多项python库，熟练掌握 pytorch、matplotlib 等中间件，曾获公司技术创新奖。',NULL),('1961995146017144833','小兰','123583277592749472','13671790753',0,NULL,'21871847981@qq.com',NULL,NULL,NULL,NULL,NULL,NULL,'1961994778084409346',NULL,'2025-08-31 11:31:10','2025-08-31 11:31:10',NULL,NULL,'','计算机','','','无','无',NULL),('1963195861045669889','张三','110101199001011234','13800138000',1,NULL,'zhangsan@example.com','1990-01-01',NULL,NULL,NULL,NULL,NULL,'1945763660796604418',NULL,'2025-09-03 19:02:22','2026-01-02 23:01:51',NULL,NULL,'北京大学','计算机科学与技术','PMP认证,Java高级工程师认证','2020年优秀员工奖,2022技术创新奖','1. XX电商平台项目 - 负责后端开发\n2. YY管理系统 - 担任项目经理','具有5年Java开发经验，熟悉Spring框架和微服务架构...',NULL);
/*!40000 ALTER TABLE `candidate` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `interview_record`
--

DROP TABLE IF EXISTS `interview_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `interview_record` (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `candidate_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '应聘者id',
  `job_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '职位名称，快照名称，原字段可能会更改',
  `answer_content` varchar(6000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '应聘者的回答内容',
  `take_time` int NOT NULL COMMENT '整个面试所花费的总时间，单位：秒',
  `result` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '面试结果详情',
  `create_time` datetime NOT NULL,
  `updated_time` datetime NOT NULL,
  `totalscore` int DEFAULT NULL,
  `offer_status` tinyint(1) DEFAULT NULL,
  `analysis` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci,
  `job_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `interviewresult` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='面试记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `interview_record`
--

LOCK TABLES `interview_record` WRITE;
/*!40000 ALTER TABLE `interview_record` DISABLE KEYS */;
INSERT INTO `interview_record` VALUES ('1945861995127098121','1961719081678761985','算法工程师','提问: 1. 什么是人工智能（AI）研究中所谓的“图灵测试”（Turing Test）？正确答案: 图灵测试由艾伦·图灵提出，是衡量机器是否表现出与人类等价或无法区分的智能行为的测试。其基本设定是：如果一个人类询问者在通过文本对话与一台机器和一个人进行交流后，无法可靠地区分机器和人类，那么这台机器就通过了测试。回答的答案: 一个测试，如果人通过打字无法分辨对方是机器还是人，就说明机器有了智能。提问: 2. 在机器学习中，“过拟合”（Overfitting）是什么意思？它通常如何避免？正确答案: 过拟合是指机器学习模型在训练数据上表现非常好，但在未见过的测试数据上表现很差的现象，意味着模型过度学习了训练数据中的细节和噪声，而非底层规律。常见的避免方法包括：1. 使用更多的训练数据；2. 采用交叉验证；3. 进行特征简化；4. 引入正则化技术；5. 使用Dropout（针对神经网络）等。回答的答案: 模型只会死记硬背训练题，不会做新题。解决方法有：多喂点数据、简化模型、用正则化等技巧防止它学太复杂。提问: 3. 人工智能的发展引发了一系列伦理担忧，其中“算法偏见”（Algorithmic Bias）指的是什么？正确答案: 算法偏见指的是计算机系统中存在的系统性、不公正的歧视性结果。这种偏见通常并非来自机器的自主意识，而是源于训练数据中本身存在的人类历史偏见、数据的不具代表性，或者算法设计者的无意识偏见。它可能导致在种族、性别、年龄等方面产生不公平的决策，例如在招聘、信贷审批或司法风险评估中。回答的答案: AI做出的决定对人（如不同性别、种族）不公平，因为它学的数据本身就有偏见，或者设计它的人无意中加入了偏见。',10,'<div> <p>完美的回答</p></div>','2025-08-30 11:50:51','2025-08-30 11:50:55',100,1,'回答完善，没有问题','1961717937057394690','http://192.168.1.5:9000/ai-interviewer/interviewresult/12345678901_20250831_115034.html'),('2008487138762735617','1957999403661033473','java工程师','提问：6. 什么是乐观锁？\n正确答案：基本概念：乐观锁是一种基于“冲突是偶然的”这一假设的锁机制。它认为在多线程环境下，数据冲突发生的概率较低，因此在操作数据时不进行加锁，而是在提交更新时检查数据是否被其他线程修改过。如果数据被修改过，则放弃当前操作或进行重试。 实现方式：乐观锁通常有两种实现方式。一种是基于版本号（Version）的实现，即在数据中增加一个版本号字段，每次更新数据时，先检查版本号是否发生变化，如果没有变化则更新数据并将版本号加1，否则放弃更新。另一种是基于时间戳的实现，原理与版本号类似，通过比较时间戳来判断数据是否被修改。 适用场景：当系统中数据冲突较少，且对性能要求较高时，适合使用乐观锁。例如，在一些读多写少的系统中，使用乐观锁可以减少锁的开销，提高系统的并发性能。\n回答内容：null\n\n提问：3. HashMap 的工作原理是什么\n正确答案：哈希函数：HashMap 使用哈希表来存储键值对。当向 HashMap 中添加键值对时，首先会通过键的 hashCode() 方法获取其哈希值，然后根据哈希值计算出该键值对在哈希表中的存储位置。哈希函数的设计目标是尽量使不同的键值对均匀地分布在哈希表中，减少碰撞的发生。 处理碰撞：由于哈希值的范围有限，不同的键可能会计算出相同的哈希值，即发生碰撞。HashMap 采用链表法来解决碰撞问题。当多个键值对的哈希值相同，它们会被存储在同一个哈希表位置的链表中。如果链表长度超过一定阈值（默认是8），则会将链表转换为红黑树，以提高查找效率。 扩容机制：当 HashMap 中的键值对数量超过一定阈值（负载因子乘以当前容量，默认负载因子是0.75）时，会触发扩容操作。扩容时，会创建一个新的更大的哈希表，通常是原容量的两倍，然后将原哈希表中的键值对重新计算哈希值并存储到新哈希表中。扩容操作会消耗较多的时间，因此合理设置初始容量可以减少扩容次数，提高性能。\n回答内容：null\n\n提问：5. 什么是悲观锁？\n正确答案：基本概念：悲观锁是一种基于“冲突是普遍的”这一假设的锁机制。它认为在多线程环境下，数据冲突是很常见的现象，因此在操作数据时，会先对数据进行加锁，以防止其他线程对数据进行修改，从而保证数据的一致性和完整性。 实现方式：在数据库中，悲观锁可以通过事务中的锁机制来实现，如使用 SELECT ... FOR UPDATE 语句在读取数据时加锁，防止其他事务修改该数据。在编程语言层面，可以使用 synchronized 关键字或 ReentrantLock 等锁类来实现悲观锁。例如，在一个方法上加 synchronized 关键字，当一个线程执行该方法时，其他线程会被阻塞，直到该线程释放锁。 适用场景：当系统中数据冲突较为频繁，且对数据一致性要求较高时，适合使用悲观锁。例如，在一些金融系统中，对账户余额等关键数据的操作需要确保高度的一致性，使用悲观锁可以有效避免数据错误。\n回答内容：null\n\n',8,'系统异常: I/O error on POST request for \"http://10.10.10.1:9997/v1/chat/completions\": Connection timed out: connect','2026-01-06 18:33:44','2026-01-06 18:33:44',0,1,'','1945763660796604418',NULL);
/*!40000 ALTER TABLE `interview_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `interviewer`
--

DROP TABLE IF EXISTS `interviewer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `interviewer` (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `ai_name` varchar(256) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数字人面试官的名称',
  `image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '数字人形象图照片',
  `create_time` datetime NOT NULL,
  `updated_time` datetime NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数字人面试官表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `interviewer`
--

LOCK TABLES `interviewer` WRITE;
/*!40000 ALTER TABLE `interviewer` DISABLE KEYS */;
INSERT INTO `interviewer` VALUES ('1945763085510062082','java工程师','http://100.90.235.16:9000/ai-interviewer/interviewer/e31e2110-7e65-40c4-b21a-52561eb71555.png','2025-07-17 16:30:45','2026-01-02 22:17:49'),('1957743991120478210','前端工程师','http://100.90.235.16:9000/ai-interviewer/interviewer/12c7b218-11ac-4098-b66c-8da3a0ee74fd.png','2025-08-19 17:58:35','2026-01-02 22:17:22'),('1957998276655742977','面试官','http://100.90.235.16:9000/ai-interviewer/interviewer/4390e968-5498-4b81-958f-8868f398aae1.png','2025-08-20 10:49:02','2026-01-02 22:17:10');
/*!40000 ALTER TABLE `interviewer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `job`
--

DROP TABLE IF EXISTS `job`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `job` (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `job_name` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '职位名称',
  `job_desc` varchar(4000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '职位描述',
  `status` int NOT NULL COMMENT '1：职位开启\n2：职位关闭',
  `interviewer_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分配的数字人面试官id，每个职位需要对应的面试官来进行面试',
  `prompt` varchar(5120) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '该职位的面试结果最终发给ChatGLM的前缀提示词',
  `create_time` datetime NOT NULL,
  `updated_time` datetime NOT NULL,
  `image` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '二维码',
  `I` int DEFAULT NULL,
  `company_info` varchar(4000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='职位信息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `job`
--

LOCK TABLES `job` WRITE;
/*!40000 ALTER TABLE `job` DISABLE KEYS */;
INSERT INTO `job` VALUES ('1945763660796604418','java工程师','java工程师',1,'1945763085510062082','假设你是一个非常厉害的经验非常丰富的Java架构师，并且也是一个java面试官。根据以下面试题的提问对:“回答内容”进行评分与简要汇总 每题评分总分为10分，对标职位为Java架构师，请根据如下内客以中文的形式为每题进行简要分析与打分并且统计一个总分，总分是每题的分数加起来的分数，你所输出的内容请用<div>等标签包裹，将总分的数字包裹在<p>标签中，如<p>总分：85</p>。 <div> <p>提问：222</p> <p>回答内容：啊啊啊啊。</p> <p>分析：面试官提出的数字222，期望回答者能够正确地重复这个数字。回答者提供的回答与问题不相关，没有给出正确的答案。</p> <p>评分：1分</p> </div> <div> <p>提问：333</p> <p>回答内容：33333。</p> <p>分析：面试官提出的数字333，期望回答者能够正确地重复这个数字。回答者虽然重复了数字，但多了一个额外的数字3，没有完全正确地重复。</p> <p>评分：2分</p> </div> <div> <p>提问：444</p> <p>回答内容：是是是是是是是是嗯。</p> <p>分析：面试官提出的数字444，期望回答者能够正确地重复这个数字。回答者虽然重复了“是”，但并没有正确地重复数字444。</p> <p>评分：1分</p> </div> </div> <p>总分：4</p>，请严格按照我给你的总分格式','2025-08-26 23:12:29','2025-07-17 16:33:02','',NULL,'年薪10万'),('1946146126472466433','test','test',1,'1945763085510062082','tset','2025-07-18 17:57:19','2025-07-18 17:52:49','',NULL,'yesey'),('1957744159660195841','前端工程师','test',1,'1957743991120478210','test','2025-08-19 17:59:15','2025-08-19 17:59:15','',NULL,'test'),('1961392402193543169','111','1111111111111111',1,'1957998276655742977','11111111111111111','2025-08-29 19:36:04','2025-08-29 19:36:04','',NULL,'年薪十万\n没有五险一金'),('1961392590521933826','111','1111111111111111',1,'1957998276655742977','11111111111111111','2025-08-29 19:36:49','2025-08-29 19:36:49','',NULL,'年薪十万\n没有五险一金'),('1961717937057394690','算法工程师','公司希望面试者有一个大模型使用的实战经历，同时也了解这方面的优化功能\\n企业希望询问内容:1. 年薪期望是多少?',1,'1941117474126954497','123','2025-08-30 17:09:38','2025-08-30 17:09:38','',NULL,NULL),('1961994778084409346','python','岗位职责：\n1、负责AI领域的软件工程化和产品开发；\n2、负责AI算法及系统的设计和实现，包括但不限于：神经网络与机器学习、计算机视觉、无人驾驶、路径规划、智能决策、推荐系统、大模型、生成式AI等；\n3、负责产品的集成和调测，以及各类工具链的开发；\n4、负责对外洞察AI领域最新趋势，包括但不限于：大模型、生成式AI、AI for coding等。\n',1,'1957743991120478210','你是一个python开发工程师的面试官，请你对用户的回答进行打分。\n','2025-08-31 11:29:42','2025-08-31 11:29:42','',NULL,'年薪10万');
/*!40000 ALTER TABLE `job` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `question_lib`
--

DROP TABLE IF EXISTS `question_lib`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `question_lib` (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `question` varchar(1280) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '面试题（文字内容）',
  `reference_answer` varchar(2048) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '参考答案',
  `ai_src` varchar(4000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '面试数字人对应的地址',
  `interviewer_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '分配的数字人面试官id，每个职位需要对应的面试官来进行面试',
  `is_on` int NOT NULL COMMENT '1：启用本题\n0：关闭本题',
  `create_time` datetime NOT NULL,
  `updated_time` datetime NOT NULL,
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='面试题库表（每个数字人面试官都会对应一些面试题）';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `question_lib`
--

LOCK TABLES `question_lib` WRITE;
/*!40000 ALTER TABLE `question_lib` DISABLE KEYS */;
INSERT INTO `question_lib` VALUES ('1945763224983252993','3. HashMap 的工作原理是什么','哈希函数：HashMap 使用哈希表来存储键值对。当向 HashMap 中添加键值对时，首先会通过键的 hashCode() 方法获取其哈希值，然后根据哈希值计算出该键值对在哈希表中的存储位置。哈希函数的设计目标是尽量使不同的键值对均匀地分布在哈希表中，减少碰撞的发生。 处理碰撞：由于哈希值的范围有限，不同的键可能会计算出相同的哈希值，即发生碰撞。HashMap 采用链表法来解决碰撞问题。当多个键值对的哈希值相同，它们会被存储在同一个哈希表位置的链表中。如果链表长度超过一定阈值（默认是8），则会将链表转换为红黑树，以提高查找效率。 扩容机制：当 HashMap 中的键值对数量超过一定阈值（负载因子乘以当前容量，默认负载因子是0.75）时，会触发扩容操作。扩容时，会创建一个新的更大的哈希表，通常是原容量的两倍，然后将原哈希表中的键值对重新计算哈希值并存储到新哈希表中。扩容操作会消耗较多的时间，因此合理设置初始容量可以减少扩容次数，提高性能。','http://100.90.235.16:9000/ai-interviewer/interviewVideo/dfc7d172-a8f0-4658-ac07-a483b0e2b473.mp4','1945763085510062082',1,'2025-07-17 16:31:18','2026-01-02 22:15:50'),('1945763301885816834','4. Collection 和 Collections 的区别是什么？','Collection：是 Java 集合框架中的一个接口，它处于集合框架的顶层，定义了集合的基本操作规范，如添加元素（add）、删除元素（remove）、判断是否包含某个元素（contains）、获取集合大小（size）等。Collection 接口有两个主要的子接口，分别是 List 和 Set。List 是有序集合，允许重复元素，如 ArrayList、LinkedList 等；Set 是无序集合，不允许重复元素，如 HashSet、TreeSet 等。 Collections：是 Java 提供的一个工具类，用于对集合进行操作。它包含了许多静态方法，可以用于对集合进行排序（如 sort 方法）、查找（如 binarySearch 方法）、反转（如 reverse 方法）、填充（如 fill 方法）等操作。Collections 类提供的是对集合的辅助操作，而不是定义集合的规范。例如，可以使用 Collections.sort(list) 对 List 集合进行排序，使用 Collections.reverse(list) 反转 List 集合中元素的顺序。','http://100.90.235.16:9000/ai-interviewer/interviewVideo/5ddf1a0f-0edc-4a39-bdfc-2bfc4dd04124.mp4','1945763085510062082',1,'2025-07-17 16:31:36','2026-01-02 22:16:09'),('1945763393040625665','5. 什么是悲观锁？','基本概念：悲观锁是一种基于“冲突是普遍的”这一假设的锁机制。它认为在多线程环境下，数据冲突是很常见的现象，因此在操作数据时，会先对数据进行加锁，以防止其他线程对数据进行修改，从而保证数据的一致性和完整性。 实现方式：在数据库中，悲观锁可以通过事务中的锁机制来实现，如使用 SELECT ... FOR UPDATE 语句在读取数据时加锁，防止其他事务修改该数据。在编程语言层面，可以使用 synchronized 关键字或 ReentrantLock 等锁类来实现悲观锁。例如，在一个方法上加 synchronized 关键字，当一个线程执行该方法时，其他线程会被阻塞，直到该线程释放锁。 适用场景：当系统中数据冲突较为频繁，且对数据一致性要求较高时，适合使用悲观锁。例如，在一些金融系统中，对账户余额等关键数据的操作需要确保高度的一致性，使用悲观锁可以有效避免数据错误。','http://100.90.235.16:9000/ai-interviewer/interviewVideo/d973e4b7-6c5b-4cbf-b916-a2b69bdf3b96.mp4','1945763085510062082',1,'2025-07-17 16:31:58','2026-01-02 22:16:19'),('1945763515665297409','6. 什么是乐观锁？','基本概念：乐观锁是一种基于“冲突是偶然的”这一假设的锁机制。它认为在多线程环境下，数据冲突发生的概率较低，因此在操作数据时不进行加锁，而是在提交更新时检查数据是否被其他线程修改过。如果数据被修改过，则放弃当前操作或进行重试。 实现方式：乐观锁通常有两种实现方式。一种是基于版本号（Version）的实现，即在数据中增加一个版本号字段，每次更新数据时，先检查版本号是否发生变化，如果没有变化则更新数据并将版本号加1，否则放弃更新。另一种是基于时间戳的实现，原理与版本号类似，通过比较时间戳来判断数据是否被修改。 适用场景：当系统中数据冲突较少，且对性能要求较高时，适合使用乐观锁。例如，在一些读多写少的系统中，使用乐观锁可以减少锁的开销，提高系统的并发性能。','http://100.90.235.16:9000/ai-interviewer/interviewVideo/62abcb23-975b-41fc-972c-0a33af02b060.mp4','1945763085510062082',1,'2025-07-17 16:32:27','2026-01-02 22:16:26');
/*!40000 ALTER TABLE `question_lib` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reexamine_record`
--

DROP TABLE IF EXISTS `reexamine_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reexamine_record` (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `index` int DEFAULT NULL,
  `question` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `answer` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reexamine_record`
--

LOCK TABLES `reexamine_record` WRITE;
/*!40000 ALTER TABLE `reexamine_record` DISABLE KEYS */;
INSERT INTO `reexamine_record` VALUES ('1961719081678761985',0,'您好！我是******大学的AI面试官，负责今天的复试环节。<br>请确保您处于安静的环境，准备好后在下方输入框中输入\"你好\"开始面试。','我不想回答你自己看吧'),('1961719081678761985',1,'当前询问内容:李四先生，您的回复态度不够端正，这会影响面试的正常进行。如果您不愿意配合，我将不得不终止本次面试。  \\n计划之后询问:','不好意思你继续吧'),('1961719081678761985',2,'当前询问内容:您好，感谢您的配合。首先，请您简要介绍一下自己，包括您的教育背景、专业技能以及您认为与岗位相关的优势。  \\\\n计划之后询问:在了解您的基本信息后，我将针对您提到的AI面试官项目进行深入探讨，随后会结合岗位需求进一步提问，最后预留时间供您提问。当前面试环节为自我介绍。','我项目经历只有求职信里面的内容'),('1961719081678761985',3,'当前询问内容:那请您详细介绍一下AI面试官项目的具体目标和您在项目中的职责。  \\n计划之后询问:该项目中使用的技术和工具，以及如何实现核心功能。','我负责python调用后端服务器的vllm功能使用chatopenai类实现，因为我主要还是只了解原理'),('1961719081678761985',4,'当前询问内容:明白了，您在项目中主要负责Python调用后端服务器的vLLM功能，并使用ChatOpenAI类实现。那么，能否请您具体说明一下，您是如何调用这些功能的？是否涉及接口设计或数据处理？  \\n计划之后询问:在了解了技术实现后，我将询问您在项目中遇到的挑战以及如何解决，随后会结合岗位需求进一步提问，最后预留时间供您提问。当前面试环节为项目经验介绍。','我主要用fastapi提供了前端接口，为chat方法用get实现，安全方面没有具体考虑因为对这些方面不了解'),('1961719081678761985',5,'当前询问内容:感谢你的回答。你在项目中使用FastAPI开发chat方法时，能否具体分享一个开发过程中遇到的挑战以及你是如何解决的？  \\n计划之后询问:项目中是否使用过数据库或缓存技术，如Redis，以及你对这些技术的理解和应用。','主要还是接口的格式问题如前端发生json格式的处理这些并不是特别了解'),('1961719081678761985',6,'当前询问内容:明白了，关于JSON格式的处理，你是否有查阅文档或寻求同事帮助来解决这个问题？  \\n计划之后询问:在AI面试官项目中，你提到使用了PyTorch，能否分享一下你在项目中是如何应用PyTorch的？','我自己学习后解决的主要查询文档看视频这些'),('1961719081678761985',7,'感谢你的回答。在AI面试官项目中，你提到使用了PyTorch，能否具体说明一下你在项目中是如何应用PyTorch的？请简明扼要地讲述一个实际的应用场景\'','这并没有使用到只是在机器学习的课程的时候使用公开数据集测试测试过，没有实战经验'),('1961719081678761985',8,'当前询问内容:了解了，你在课程中使用PyTorch进行公开数据集测试时，有没有尝试过调整模型参数或优化模型性能？如果有，能否简单分享一下你的方法和结果？  \\n计划之后询问:在AI面试官项目中，除了FastAPI和PyTorch，是否还使用过其他技术或工具？如果有，能否简要介绍一下它们的作用？','有主要还是调节a和weight先调节学习速率较小然后通过每次epoch后的loss看变化来调整'),('1961719081678761985',9,'明白了，你在调节模型参数时主要关注loss的变化，这有助于优化模型性能。在AI面试官项目中，除了FastAPI和PyTorch，是否还使用过其他技术或工具？如果有，能否简要介绍一下它们的作用？  \\n','没有了'),('1961719081678761985',10,'我注意到您提到参与过AI面试官项目，请问在该项目中是否有使用大模型？如果有，能否简要说明您在使用过程中遇到的主要挑战以及如何优化模型性能？','你好'),('1961719081678761985',11,'我注意到您提到参与过AI面试官项目，请问在该项目中是否有使用大模型？如果有，能否简要说明您在使用过程中遇到的主要挑战以及如何优化模型性能？','你好你好。'),('1961719081678761985',12,'我注意到您提到参与过AI面试官项目，请问在该项目中是否有使用大模型？如果有，能否简要说明您在使用过程中遇到的主要挑战以及如何优化模型性能？','好的好的。');
/*!40000 ALTER TABLE `reexamine_record` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `reexamine_summary`
--

DROP TABLE IF EXISTS `reexamine_summary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `reexamine_summary` (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
  `summary_tmp_ai` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作为ai的chat_history用',
  `summary_tmp_answer` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '作为面试者的chat_history用',
  `end_question` varchar(1000) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '总结',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reexamine_summary`
--

LOCK TABLES `reexamine_summary` WRITE;
/*!40000 ALTER TABLE `reexamine_summary` DISABLE KEYS */;
INSERT INTO `reexamine_summary` VALUES ('1961719081678761985','历史摘要｜用户关键信息，从这次面试中得到的，如果已经是面试者信息里已经有的内容则不用提及  \\n面试者李四在AI面试官项目中主要使用了FastAPI进行接口开发，但在JSON格式处理方面经验有限，主要依靠自学和文档解决。在PyTorch方面仅限于课程中的公开数据集测试，缺乏实战经验，但具备基本的模型参数调节能力，如学习率调整和loss监控。  \\n计划提问 | 项目中是否使用过数据库或缓存技术，如Redis，以及你对这些技术的理解和应用。  \\n结束计划 | 当前轮数为9，剩余1轮，优先完成岗位需求相关问题（如年薪期望），并尽快进入解答环节。轮数:9','','当前询问内容:我注意到您提到参与过AI面试官项目，请问在该项目中是否有使用大模型？如果有，能否简要说明您在使用过程中遇到的主要挑战以及如何优化模型性能？\n计划之后询问:如果回答中提及大模型使用，可以进一步询问具体优化方法，如模型压缩或推理加速；如果未涉及大模型，可以确认是否具备相关经验，并询问岗位的年薪期望。');
/*!40000 ALTER TABLE `reexamine_summary` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-01-06 18:51:19
