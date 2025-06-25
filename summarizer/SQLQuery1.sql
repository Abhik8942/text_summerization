USE JJ
GO

SELECT @@SERVERNAME

-- Users table
--CREATE TABLE Users (
--    UserID INT PRIMARY KEY IDENTITY(1,1),
--    Username NVARCHAR(50) UNIQUE NOT NULL,
--    Email NVARCHAR(100) UNIQUE NOT NULL,
--    PasswordHash NVARCHAR(255) NOT NULL
--);

-- Summarization history table
CREATE TABLE SummarizationHistory (
    HistoryID INT PRIMARY KEY IDENTITY(1,1),
    UserID INT FOREIGN KEY REFERENCES Users(UserID),
    SummaryType NVARCHAR(20),  -- 'text' or 'video'
    OriginalContent NVARCHAR(MAX),
    Summary NVARCHAR(MAX),
    DateCreated DATETIME DEFAULT GETDATE()
);

select * from Users;

select * from SummarizationHistory;


drop table SummarizationHistory;
drop table Users;


-- Users table
CREATE TABLE Users (
    UserID INT PRIMARY KEY IDENTITY(1,1),
    FirstName NVARCHAR(50) NOT NULL CHECK (LEN(FirstName) >= 2 AND FirstName LIKE '%[A-Za-z]%'),
    LastName NVARCHAR(50) NOT NULL CHECK (LEN(LastName) >= 2 AND LastName LIKE '%[A-Za-z]%'),
    Username NVARCHAR(50) UNIQUE NOT NULL CHECK (Username LIKE '[A-Za-z0-9_]%'),
    Email NVARCHAR(100) UNIQUE NOT NULL CHECK (Email LIKE '%_@__%.__%'),
    PhoneNumber CHAR(10) NOT NULL CHECK (PhoneNumber LIKE '[0-9]%'),
    PasswordHash NVARCHAR(255) NOT NULL, -- Store hashed passwords for security
    CreatedAt DATETIME DEFAULT GETDATE(), -- Optional field to track user creation time
    UpdatedAt DATETIME DEFAULT GETDATE() -- Optional field to track updates
);



EXEC sp_help Users;
EXEC sp_help SummarizationHistory;
