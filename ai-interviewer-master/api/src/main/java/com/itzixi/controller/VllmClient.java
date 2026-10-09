package com.itzixi.controller;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import org.springframework.http.*;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

public class VllmClient {
    private static final String VLLM_URL = "http://10.10.10.1:9997/v1/chat/completions";
    private static final String API_KEY = System.getenv("VLLM_API_KEY");
    private static final String MODEL_NAME = "Qwen3-32B";

    public static void main(String[] args) {
        String prompt = "假设你是一个非常厉害的经验非常丰富的Java架构师，并且也是一个java面试官。根据以下面试题的提问对:“回答内容”进行评分与简要汇总 每题评分总分为10分，对标职位为Java架构师，请根据如下内客以中文的形式为每题进行简要分析与打分并且统计一个总分，总分是每题的分数加起来的分数，你所输出的内容请用<div>等标签包裹，将总分的数字包裹在<p>标签中，如<p>总分：85</p>。 <div> <p>提问：222</p> <p>回答内容：啊啊啊啊。</p> <p>分析：面试官提出的数字222，期望回答者能够正确地重复这个数字。回答者提供的回答与问题不相关，没有给出正确的答案。</p> <p>评分：1分</p> </div> <div> <p>提问：333</p> <p>回答内容：33333。</p> <p>分析：面试官提出的数字333，期望回答者能够正确地重复这个数字。回答者虽然重复了数字，但多了一个额外的数字3，没有完全正确地重复。</p> <p>评分：2分</p> </div> <div> <p>提问：444</p> <p>回答内容：是是是是是是是是嗯。</p> <p>分析：面试官提出的数字444，期望回答者能够正确地重复这个数字。回答者虽然重复了“是”，但并没有正确地重复数字444。</p> <p>评分：1分</p> </div> </div> <p>总分：4</p>，请严格按照我给你的总分格式\n" +
                "\n" +
                "提问：6. 什么是乐观锁？\n" +
                "正确答案：基本概念：乐观锁是一种基于“冲突是偶然的”这一假设的锁机制。它认为在多线程环境下，数据冲突发生的概率较低，因此在操作数据时不进行加锁，而是在提交更新时检查数据是否被其他线程修改过。如果数据被修改过，则放弃当前操作或进行重试。 实现方式：乐观锁通常有两种实现方式。一种是基于版本号（Version）的实现，即在数据中增加一个版本号字段，每次更新数据时，先检查版本号是否发生变化，如果没有变化则更新数据并将版本号加1，否则放弃更新。另一种是基于时间戳的实现，原理与版本号类似，通过比较时间戳来判断数据是否被修改。 适用场景：当系统中数据冲突较少，且对性能要求较高时，适合使用乐观锁。例如，在一些读多写少的系统中，使用乐观锁可以减少锁的开销，提高系统的并发性能。\n" +
                "回答内容：乐观锁是一种基于冲突是普遍的这一假设索机制。\n" +
                "\n" +
                "提问：3. HashMap 的工作原理是什么\n" +
                "正确答案：哈希函数：HashMap 使用哈希表来存储键值对。当向 HashMap 中添加键值对时，首先会通过键的 hashCode() 方法获取其哈希值，然后根据哈希值计算出该键值对在哈希表中的存储位置。哈希函数的设计目标是尽量使不同的键值对均匀地分布在哈希表中，减少碰撞的发生。 处理碰撞：由于哈希值的范围有限，不同的键可能会计算出相同的哈希值，即发生碰撞。HashMap 采用链表法来解决碰撞问题。当多个键值对的哈希值相同，它们会被存储在同一个哈希表位置的链表中。如果链表长度超过一定阈值（默认是8），则会将链表转换为红黑树，以提高查找效率。 扩容机制：当 HashMap 中的键值对数量超过一定阈值（负载因子乘以当前容量，默认负载因子是0.75）时，会触发扩容操作。扩容时，会创建一个新的更大的哈希表，通常是原容量的两倍，然后将原哈希表中的键值对重新计算哈希值并存储到新哈希表中。扩容操作会消耗较多的时间，因此合理设置初始容量可以减少扩容次数，提高性能。\n" +
                "回答内容：哈西迈不逊哈希表达村市竞支队。\n" +
                "\n" +
                "提问：5. 什么是悲观锁？\n" +
                "正确答案：基本概念：悲观锁是一种基于“冲突是普遍的”这一假设的锁机制。它认为在多线程环境下，数据冲突是很常见的现象，因此在操作数据时，会先对数据进行加锁，以防止其他线程对数据进行修改，从而保证数据的一致性和完整性。 实现方式：在数据库中，悲观锁可以通过事务中的锁机制来实现，如使用 SELECT ... FOR UPDATE 语句在读取数据时加锁，防止其他事务修改该数据。在编程语言层面，可以使用 synchronized 关键字或 ReentrantLock 等锁类来实现悲观锁。例如，在一个方法上加 synchronized 关键字，当一个线程执行该方法时，其他线程会被阻塞，直到该线程释放锁。 适用场景：当系统中数据冲突较为频繁，且对数据一致性要求较高时，适合使用悲观锁。例如，在一些金融系统中，对账户余额等关键数据的操作需要确保高度的一致性，使用悲观锁可以有效避免数据错误。\n" +
                "回答内容：被一关锁是一种基于冲度是普遍的这一假设的所机制。"; // 此处是你的长提示词
        String response = queryModel(prompt);
        System.out.println("模型回复: \n" + response);
    }

    public static String queryModel(String prompt) {
        RestTemplate restTemplate = new RestTemplate();

        // 设置请求头
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("Authorization", "Bearer " + API_KEY);

        // 使用JsonObject构建请求体，避免拼接错误
        JsonObject requestBodyJson = new JsonObject();
        requestBodyJson.addProperty("model", MODEL_NAME);

        JsonArray messagesArray = new JsonArray();
        JsonObject messageObject = new JsonObject();
        messageObject.addProperty("role", "user");
        messageObject.addProperty("content", prompt);
        messagesArray.add(messageObject);

        requestBodyJson.add("messages", messagesArray);
        String requestBody = requestBodyJson.toString();

        // 封装请求
        HttpEntity<String> requestEntity = new HttpEntity<>(requestBody, headers);

        try {
            // 发送请求
            ResponseEntity<String> responseEntity = restTemplate.exchange(
                    VLLM_URL,
                    HttpMethod.POST,
                    requestEntity,
                    String.class
            );

            // 处理成功响应
            if (responseEntity.getStatusCode() == HttpStatus.OK) {
                JsonObject root = JsonParser.parseString(responseEntity.getBody()).getAsJsonObject();
                JsonArray choices = root.getAsJsonArray("choices");
                JsonObject firstChoice = choices.get(0).getAsJsonObject();
                JsonObject message = firstChoice.getAsJsonObject("message");
                return message.get("content").getAsString();
            } else {
                return "HTTP错误: " + responseEntity.getStatusCode();
            }
        } catch (HttpClientErrorException e) {
            System.err.println("客户端错误: " + e.getStatusCode());
            System.err.println("响应详情: " + e.getResponseBodyAsString());
            return "请求失败: " + e.getStatusText();
        } catch (Exception e) {
            e.printStackTrace();
            return "系统异常: " + e.getMessage();
        }
    }
}