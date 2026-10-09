package com.itzixi.service;

import com.itzixi.pojo.User;

public interface UserService {
    User findByUsername(String username);
    int save(User user);
    User findById(Integer id);

    int updatePassword(User user);

}
