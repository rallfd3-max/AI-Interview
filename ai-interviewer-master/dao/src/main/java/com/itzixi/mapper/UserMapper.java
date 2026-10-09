package com.itzixi.mapper;

import com.itzixi.pojo.User;
import org.apache.ibatis.annotations.*;

@Mapper
public interface UserMapper {
    @Select("SELECT * FROM admin WHERE username = #{username}")
    User findByUsername(@Param("username") String username);

    @Insert("INSERT INTO admin(username, password) VALUES(#{username}, #{password})")
    int save(User user);
    @Select("SELECT * FROM admin WHERE id = #{id}")
    User findById(Integer id);

    @Update("UPDATE admin SET password = #{password} WHERE id = #{id}")
    int updatePassword(User user);
}
